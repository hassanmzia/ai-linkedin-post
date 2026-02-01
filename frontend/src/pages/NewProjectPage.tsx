import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsAPI, templatesAPI } from '../services/api';
import type { PostTemplate } from '../types';
import toast from 'react-hot-toast';

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'inspirational', label: 'Inspirational' },
  { value: 'educational', label: 'Educational' },
  { value: 'storytelling', label: 'Storytelling' },
  { value: 'controversial', label: 'Hot Take' },
  { value: 'humorous', label: 'Humorous' },
];

export default function NewProjectPage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<PostTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: '',
    topic: '',
    template: '',
    tone: 'professional',
    target_audience: '',
    target_word_count_min: 150,
    target_word_count_max: 300,
    include_hashtags: true,
    include_cta: true,
    include_emoji: false,
    language: 'English',
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = useState('');
  const [autoGenerate, setAutoGenerate] = useState(true);

  useEffect(() => {
    templatesAPI.list().then(({ data }) => setTemplates(data.results || data)).catch(() => {});
  }, []);

  const update = (field: string, value: any) => setForm((prev) => ({ ...prev, [field]: value }));

  const addTag = () => {
    if (tagInput.trim() && !form.tags.includes(tagInput.trim())) {
      update('tags', [...form.tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.topic) { toast.error('Title and topic are required'); return; }
    setLoading(true);
    try {
      const { data } = await projectsAPI.create({
        ...form,
        template: form.template || null,
      });
      const projectId = data.id;

      if (autoGenerate) {
        await projectsAPI.generate(projectId);
        toast.success('Project created and generation started!');
      } else {
        toast.success('Project created');
      }

      navigate(`/projects/${projectId}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Post Project</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic info */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Basic Information</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Title</label>
            <input type="text" value={form.title} onChange={(e) => update('title', e.target.value)}
              className="input-field" placeholder="E.g., AI Tools for Productivity" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Topic / Prompt</label>
            <textarea value={form.topic} onChange={(e) => update('topic', e.target.value)}
              className="input-field min-h-[100px]" rows={4}
              placeholder="Describe what the LinkedIn post should be about..." required />
            <p className="text-xs text-gray-400 mt-1">Be specific - the AI agents will research and create content based on this</p>
          </div>
        </div>

        {/* Template selection */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Template (Optional)</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <button type="button" onClick={() => update('template', '')}
              className={`p-3 rounded-lg border text-left text-sm transition-all ${!form.template ? 'border-linkedin-500 bg-linkedin-50' : 'border-gray-200 hover:border-gray-300'}`}>
              <p className="font-medium">No Template</p>
              <p className="text-xs text-gray-500">Free-form</p>
            </button>
            {templates.map((t) => (
              <button key={t.id} type="button" onClick={() => { update('template', t.id); update('tone', t.tone); }}
                className={`p-3 rounded-lg border text-left text-sm transition-all ${form.template === t.id ? 'border-linkedin-500 bg-linkedin-50' : 'border-gray-200 hover:border-gray-300'}`}>
                <p className="font-medium">{t.name}</p>
                <p className="text-xs text-gray-500">{t.tone} / {t.category}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Configuration */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
              <select value={form.tone} onChange={(e) => update('tone', e.target.value)} className="input-field">
                {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Audience</label>
              <input type="text" value={form.target_audience} onChange={(e) => update('target_audience', e.target.value)}
                className="input-field" placeholder="E.g., tech professionals, marketers" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Words</label>
              <input type="number" value={form.target_word_count_min} onChange={(e) => update('target_word_count_min', Number(e.target.value))}
                className="input-field" min={50} max={1000} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Words</label>
              <input type="number" value={form.target_word_count_max} onChange={(e) => update('target_word_count_max', Number(e.target.value))}
                className="input-field" min={100} max={2000} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <input type="text" value={form.language} onChange={(e) => update('language', e.target.value)}
                className="input-field" />
            </div>
          </div>

          <div className="flex flex-wrap gap-6 pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.include_hashtags} onChange={(e) => update('include_hashtags', e.target.checked)}
                className="rounded text-linkedin-500 focus:ring-linkedin-500" />
              <span className="text-sm text-gray-700">Include Hashtags</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.include_cta} onChange={(e) => update('include_cta', e.target.checked)}
                className="rounded text-linkedin-500 focus:ring-linkedin-500" />
              <span className="text-sm text-gray-700">Include Call-to-Action</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.include_emoji} onChange={(e) => update('include_emoji', e.target.checked)}
                className="rounded text-linkedin-500 focus:ring-linkedin-500" />
              <span className="text-sm text-gray-700">Include Emoji</span>
            </label>
          </div>
        </div>

        {/* Tags */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Tags</h2>
          <div className="flex gap-2">
            <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              className="input-field flex-1" placeholder="Add tag..." />
            <button type="button" onClick={addTag} className="btn-secondary">Add</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {form.tags.map((tag) => (
              <span key={tag} className="badge bg-gray-100 text-gray-700 px-3 py-1">
                {tag}
                <button type="button" onClick={() => update('tags', form.tags.filter((t) => t !== tag))}
                  className="ml-1.5 text-gray-400 hover:text-red-500">&times;</button>
              </span>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={autoGenerate} onChange={(e) => setAutoGenerate(e.target.checked)}
              className="rounded text-linkedin-500 focus:ring-linkedin-500" />
            <span className="text-sm text-gray-700">Auto-generate post after creation</span>
          </label>
          <div className="flex gap-3">
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Creating...' : autoGenerate ? 'Create & Generate' : 'Create Project'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
