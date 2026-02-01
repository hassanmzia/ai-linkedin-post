import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import type { PostProject } from '../types';
import toast from 'react-hot-toast';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  researching: 'bg-blue-100 text-blue-700',
  writing: 'bg-indigo-100 text-indigo-700',
  reviewing: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  published: 'bg-emerald-100 text-emerald-800',
  failed: 'bg-red-100 text-red-700',
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<PostProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [search, setSearch] = useState('');

  const load = () => {
    const params: Record<string, string> = {};
    if (filter) params.status = filter;
    if (search) params.search = search;
    projectsAPI.list(params).then(({ data }) => {
      setProjects(data.results || data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filter, search]);

  const toggleFav = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await projectsAPI.toggleFavorite(id);
      load();
    } catch { toast.error('Failed to toggle favorite'); }
  };

  const deleteProject = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm('Delete this project?')) return;
    try {
      await projectsAPI.delete(id);
      load();
      toast.success('Project deleted');
    } catch { toast.error('Failed to delete'); }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
        <Link to="/projects/new" className="btn-primary">+ New Project</Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input type="text" placeholder="Search projects..." value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field max-w-xs" />
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="input-field max-w-[180px]">
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="approved">Approved</option>
          <option value="published">Published</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Project list */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No projects found</p>
          <Link to="/projects/new" className="btn-primary">Create your first project</Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 truncate">{p.title}</h3>
                    <span className={`badge ${STATUS_COLORS[p.status]}`}>{p.status}</span>
                    {p.is_favorite && <span className="text-yellow-500">*</span>}
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-2">{p.topic}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>Tone: {p.tone}</span>
                    {p.groundedness_score != null && <span>Score: {p.groundedness_score}/5</span>}
                    {p.draft_count ? <span>{p.draft_count} drafts</span> : null}
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  </div>
                  {p.latest_draft_preview && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-1 italic">"{p.latest_draft_preview}"</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={(e) => toggleFav(p.id, e)} className="text-gray-400 hover:text-yellow-500 p-1">
                    <svg className="w-5 h-5" fill={p.is_favorite ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                    </svg>
                  </button>
                  <button onClick={(e) => deleteProject(p.id, e)} className="text-gray-400 hover:text-red-500 p-1">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                    </svg>
                  </button>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
