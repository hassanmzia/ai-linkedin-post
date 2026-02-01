import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { useAgentStream } from '../hooks/useAgentStream';
import type { PostProject } from '../types';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700', researching: 'bg-blue-100 text-blue-700',
  writing: 'bg-indigo-100 text-indigo-700', reviewing: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700', published: 'bg-emerald-100 text-emerald-800',
  failed: 'bg-red-100 text-red-700',
};

const AGENT_COLORS: Record<string, string> = {
  supervisor: 'border-indigo-400 bg-indigo-50', researcher: 'border-emerald-400 bg-emerald-50',
  writer: 'border-blue-400 bg-blue-50', critic: 'border-amber-400 bg-amber-50',
  evaluator: 'border-purple-400 bg-purple-50',
};

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<PostProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingPost, setEditingPost] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [feedback, setFeedback] = useState('');
  const [tab, setTab] = useState<'post' | 'workflow' | 'research' | 'drafts'>('post');
  const agentStream = useAgentStream(id || null);

  const load = useCallback(() => {
    if (!id) return;
    projectsAPI.get(id).then(({ data }) => {
      setProject(data);
      setEditContent(data.final_post || '');
      setLoading(false);
    }).catch(() => { setLoading(false); toast.error('Project not found'); navigate('/projects'); });
  }, [id, navigate]);

  useEffect(() => { load(); }, [load]);

  // Reload when agent stream completes
  useEffect(() => {
    if (agentStream.finalPost || agentStream.error) {
      setTimeout(load, 1000);
    }
  }, [agentStream.finalPost, agentStream.error, load]);

  const handleGenerate = async () => {
    try {
      const { data } = await projectsAPI.generate(id!);
      agentStream.subscribe(data.task_id);
      toast.success('Generation started!');
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to start generation');
    }
  };

  const handleRegenerate = async () => {
    try {
      const { data } = await projectsAPI.regenerate(id!, feedback);
      agentStream.subscribe(data.task_id);
      setFeedback('');
      toast.success('Regeneration started!');
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed');
    }
  };

  const handleEvaluate = async () => {
    try {
      await projectsAPI.evaluate(id!);
      toast.success('Evaluation started');
      setTimeout(load, 5000);
    } catch { toast.error('Failed to evaluate'); }
  };

  const handlePublish = async () => {
    try {
      await projectsAPI.publish(id!);
      toast.success('Post marked as published!');
      load();
    } catch { toast.error('Failed'); }
  };

  const handleSaveEdit = async () => {
    try {
      await projectsAPI.updatePost(id!, editContent);
      setEditingPost(false);
      toast.success('Post updated');
      load();
    } catch { toast.error('Failed to save'); }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(project?.final_post || '');
    toast.success('Copied to clipboard!');
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Loading...</div>;
  if (!project) return null;

  const isGenerating = ['researching', 'writing', 'reviewing'].includes(project.status) || agentStream.isRunning;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            <span className={`badge ${STATUS_COLORS[project.status]}`}>{project.status}</span>
          </div>
          <p className="text-gray-500">{project.topic}</p>
          <div className="flex gap-4 mt-2 text-sm text-gray-400">
            <span>Tone: {project.tone}</span>
            <span>Audience: {project.target_audience || 'General'}</span>
            <span>Language: {project.language}</span>
            {project.groundedness_score != null && (
              <span className="font-medium text-purple-600">Groundedness: {project.groundedness_score}/5</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {project.status === 'draft' && (
            <button onClick={handleGenerate} disabled={isGenerating} className="btn-primary">
              {isGenerating ? 'Generating...' : 'Generate Post'}
            </button>
          )}
          {project.final_post && project.status !== 'published' && (
            <button onClick={handlePublish} className="btn-primary">Mark as Published</button>
          )}
        </div>
      </div>

      {/* Agent Stream - Live Progress */}
      {(agentStream.isRunning || agentStream.steps.length > 0) && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            Agent Workflow Progress
            {agentStream.isRunning && (
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            )}
          </h2>
          <div className="space-y-3">
            {agentStream.steps.map((step, i) => (
              <div key={i} className={`p-3 rounded-lg border-l-4 ${AGENT_COLORS[step.agent] || 'border-gray-300 bg-gray-50'} ${agentStream.isRunning && i === agentStream.steps.length - 1 ? 'agent-step-active' : ''}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium capitalize text-sm">{step.agent}</span>
                    <span className="text-xs text-gray-500">Step {step.step}</span>
                  </div>
                  {step.data.duration_ms && (
                    <span className="text-xs text-gray-400">{step.data.duration_ms}ms</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {step.data.decision || step.data.task || step.data.findings_preview || step.data.draft_preview || step.data.feedback_preview || ''}
                </p>
              </div>
            ))}
          </div>
          {agentStream.error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {agentStream.error}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {(['post', 'workflow', 'research', 'drafts'] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors capitalize ${tab === t ? 'border-linkedin-500 text-linkedin-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab: Final Post */}
      {tab === 'post' && (
        <div className="space-y-4">
          {project.final_post ? (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Final Post</h2>
                <div className="flex gap-2">
                  <button onClick={copyToClipboard} className="btn-secondary text-sm">Copy</button>
                  <button onClick={() => setEditingPost(!editingPost)} className="btn-secondary text-sm">
                    {editingPost ? 'Cancel' : 'Edit'}
                  </button>
                </div>
              </div>
              {editingPost ? (
                <div>
                  <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)}
                    className="input-field min-h-[300px] font-mono text-sm" rows={15} />
                  <div className="flex justify-end mt-3">
                    <button onClick={handleSaveEdit} className="btn-primary">Save Changes</button>
                  </div>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none whitespace-pre-wrap bg-gray-50 p-4 rounded-lg">
                  <ReactMarkdown>{project.final_post}</ReactMarkdown>
                </div>
              )}
              <div className="flex items-center gap-3 mt-4 text-sm text-gray-500">
                <span>{project.final_post.split(/\s+/).length} words</span>
                {project.groundedness_score != null && (
                  <span className="badge bg-purple-100 text-purple-700">
                    Groundedness: {project.groundedness_score}/5
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-gray-500 mb-4">No post generated yet</p>
              <button onClick={handleGenerate} disabled={isGenerating} className="btn-primary">
                {isGenerating ? 'Generating...' : 'Generate Post'}
              </button>
            </div>
          )}

          {/* Groundedness Report */}
          {project.groundedness_report && (
            <div className="card">
              <h3 className="font-semibold mb-3">Groundedness Report</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-green-700 mb-2">Supported Claims</h4>
                  <ul className="text-sm space-y-1">
                    {project.groundedness_report.supported?.map((c, i) => (
                      <li key={i} className="text-gray-600">- {c}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-red-700 mb-2">Unsupported Claims</h4>
                  <ul className="text-sm space-y-1">
                    {project.groundedness_report.unsupported?.map((c, i) => (
                      <li key={i} className="text-gray-600">- {c}</li>
                    ))}
                  </ul>
                </div>
              </div>
              {project.groundedness_report.notes && (
                <p className="text-sm text-gray-500 mt-3 italic">{project.groundedness_report.notes}</p>
              )}
            </div>
          )}

          {/* Regenerate */}
          {project.final_post && (
            <div className="card">
              <h3 className="font-semibold mb-3">Regenerate with Feedback</h3>
              <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)}
                className="input-field" rows={3} placeholder="Optional: Add specific feedback for the next generation..." />
              <div className="flex gap-2 mt-3">
                <button onClick={handleRegenerate} disabled={isGenerating} className="btn-primary">
                  {isGenerating ? 'Generating...' : 'Regenerate'}
                </button>
                <button onClick={handleEvaluate} className="btn-secondary">Re-evaluate Groundedness</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Workflow */}
      {tab === 'workflow' && (
        <div className="space-y-4">
          {project.runs?.map((run) => (
            <div key={run.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold">Run: {run.id.slice(0, 8)}</h3>
                  <p className="text-sm text-gray-500">
                    {run.status} - {run.total_revisions} revisions
                  </p>
                </div>
                <span className={`badge ${run.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {run.status}
                </span>
              </div>
              <div className="space-y-2">
                {run.steps?.map((step) => (
                  <div key={step.id} className={`p-3 rounded-lg border-l-4 ${AGENT_COLORS[step.agent_name] || 'border-gray-300 bg-gray-50'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm capitalize">{step.agent_name} (Step {step.step_number})</span>
                      {step.duration_ms && <span className="text-xs text-gray-400">{step.duration_ms}ms</span>}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{step.decision}</p>
                  </div>
                ))}
              </div>
              {run.error_message && (
                <div className="mt-3 p-3 bg-red-50 rounded-lg text-red-700 text-sm">{run.error_message}</div>
              )}
            </div>
          ))}
          {!project.runs?.length && <p className="text-gray-500 text-center py-8">No workflow runs yet</p>}
        </div>
      )}

      {/* Tab: Research */}
      {tab === 'research' && (
        <div className="space-y-4">
          {project.findings?.map((f) => (
            <div key={f.id} className="card">
              <h3 className="font-semibold mb-2">Query: {f.query}</h3>
              <div className="prose prose-sm max-w-none text-gray-600 whitespace-pre-wrap">
                <ReactMarkdown>{f.summary}</ReactMarkdown>
              </div>
              {f.sources?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-1">Sources:</p>
                  {f.sources.map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                      className="block text-xs text-linkedin-500 hover:underline truncate">{s.title || s.url}</a>
                  ))}
                </div>
              )}
            </div>
          ))}
          {!project.findings?.length && <p className="text-gray-500 text-center py-8">No research findings yet</p>}
        </div>
      )}

      {/* Tab: Drafts */}
      {tab === 'drafts' && (
        <div className="space-y-4">
          {project.drafts?.map((d) => (
            <div key={d.id} className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">Version {d.version}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">{d.word_count} words</span>
                  {d.is_approved && <span className="badge bg-green-100 text-green-700">Approved</span>}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap">{d.content}</div>
              {d.critique_notes && (
                <div className="mt-3 p-3 bg-amber-50 rounded-lg border-l-4 border-amber-400">
                  <p className="text-xs font-medium text-amber-700 mb-1">Critique:</p>
                  <p className="text-sm text-gray-600">{d.critique_notes}</p>
                </div>
              )}
            </div>
          ))}
          {!project.drafts?.length && <p className="text-gray-500 text-center py-8">No drafts yet</p>}
        </div>
      )}
    </div>
  );
}
