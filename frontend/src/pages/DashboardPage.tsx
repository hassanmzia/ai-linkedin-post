import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../services/api';
import type { DashboardStats } from '../types';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardAPI.stats().then(({ data }) => { setStats(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-gray-500">Loading dashboard...</div></div>;

  const statCards = [
    { label: 'Total Projects', value: stats?.total_projects ?? 0, color: 'bg-blue-500' },
    { label: 'Published Posts', value: stats?.published_posts ?? 0, color: 'bg-green-500' },
    { label: 'Avg Groundedness', value: stats?.avg_groundedness != null ? `${stats.avg_groundedness.toFixed(1)}/5` : 'N/A', color: 'bg-purple-500' },
    { label: 'This Week', value: stats?.posts_this_week ?? 0, color: 'bg-orange-500' },
    { label: 'This Month', value: stats?.posts_this_month ?? 0, color: 'bg-cyan-500' },
    { label: 'Total Revisions', value: stats?.total_revisions ?? 0, color: 'bg-pink-500' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your LinkedIn post creation activity</p>
        </div>
        <Link to="/projects/new" className="btn-primary">
          + New Post Project
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="card">
            <div className={`w-10 h-10 rounded-lg ${stat.color} flex items-center justify-center mb-3`}>
              <span className="text-white text-lg font-bold">{typeof stat.value === 'number' ? (stat.value > 99 ? '99+' : stat.value) : '#'}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Agent Workflow visualization */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Multi-Agent Workflow</h2>
        <div className="flex items-center justify-center gap-4 flex-wrap py-6">
          {['Supervisor', 'Researcher', 'Writer', 'Critic', 'Evaluator'].map((agent, i) => (
            <div key={agent} className="flex items-center gap-4">
              <div className="text-center">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold ${
                  ['bg-indigo-500', 'bg-emerald-500', 'bg-blue-500', 'bg-amber-500', 'bg-purple-500'][i]
                }`}>
                  {agent[0]}
                </div>
                <p className="text-xs font-medium mt-2 text-gray-700">{agent}</p>
              </div>
              {i < 4 && (
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
              )}
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-500 text-center">
          Each post goes through Supervisor orchestration, Research gathering, Writing, Critique review, and Groundedness evaluation
        </p>
      </div>

      {/* Recent projects */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
          <Link to="/projects" className="text-sm text-linkedin-500 hover:underline">View all</Link>
        </div>
        {stats?.recent_projects?.length ? (
          <div className="space-y-3">
            {stats.recent_projects.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{p.title}</p>
                  <p className="text-sm text-gray-500 truncate">{p.topic}</p>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <StatusBadge status={p.status} />
                  {p.groundedness_score != null && (
                    <span className="badge bg-purple-100 text-purple-700">{p.groundedness_score}/5</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No projects yet. Create your first post!</p>
        )}
      </div>

      {/* Top tones */}
      {stats?.top_tones?.length ? (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Most Used Tones</h2>
          <div className="flex gap-3 flex-wrap">
            {stats.top_tones.map((t) => (
              <div key={t.tone} className="badge bg-gray-100 text-gray-700 px-3 py-1.5 text-sm">
                {t.tone} ({t.count})
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    researching: 'bg-blue-100 text-blue-700',
    writing: 'bg-indigo-100 text-indigo-700',
    reviewing: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    published: 'bg-emerald-100 text-emerald-800',
    failed: 'bg-red-100 text-red-700',
  };
  return <span className={`badge ${colors[status] || colors.draft}`}>{status}</span>;
}
