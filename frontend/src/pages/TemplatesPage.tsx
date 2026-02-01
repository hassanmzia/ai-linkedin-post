import { useEffect, useState } from 'react';
import { templatesAPI } from '../services/api';
import type { PostTemplate } from '../types';
import toast from 'react-hot-toast';

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<PostTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '', description: '', tone: 'professional', category: 'tech',
    structure_prompt: '', example_post: '',
  });

  const load = () => {
    templatesAPI.list().then(({ data }) => { setTemplates(data.results || data); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await templatesAPI.create(form);
      toast.success('Template created');
      setShowForm(false);
      setForm({ name: '', description: '', tone: 'professional', category: 'tech', structure_prompt: '', example_post: '' });
      load();
    } catch { toast.error('Failed to create template'); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return;
    try {
      await templatesAPI.delete(id);
      toast.success('Template deleted');
      load();
    } catch { toast.error('Cannot delete system templates'); }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Post Templates</h1>
          <p className="text-gray-500 mt-1">Reusable structures for your LinkedIn posts</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ New Template'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card space-y-4">
          <h2 className="text-lg font-semibold">Create Template</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
              <select value={form.tone} onChange={(e) => setForm({ ...form, tone: e.target.value })} className="input-field">
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="inspirational">Inspirational</option>
                <option value="educational">Educational</option>
                <option value="storytelling">Storytelling</option>
                <option value="controversial">Hot Take</option>
                <option value="humorous">Humorous</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-field">
                <option value="tech">Technology</option>
                <option value="leadership">Leadership</option>
                <option value="career">Career Growth</option>
                <option value="startup">Startup</option>
                <option value="ai_ml">AI / ML</option>
                <option value="productivity">Productivity</option>
                <option value="marketing">Marketing</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Structure Instructions</label>
            <textarea value={form.structure_prompt} onChange={(e) => setForm({ ...form, structure_prompt: e.target.value })}
              className="input-field" rows={4} placeholder="Describe the structure the writer agent should follow..." required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Example Post (Optional)</label>
            <textarea value={form.example_post} onChange={(e) => setForm({ ...form, example_post: e.target.value })}
              className="input-field" rows={3} placeholder="An example post following this template..." />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary">Create Template</button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((t) => (
          <div key={t.id} className="card">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900">{t.name}</h3>
                  {t.is_system && <span className="badge bg-blue-100 text-blue-700">System</span>}
                </div>
                <p className="text-sm text-gray-500">{t.description}</p>
              </div>
              {!t.is_system && (
                <button onClick={() => handleDelete(t.id)} className="text-gray-400 hover:text-red-500">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <div className="flex gap-2 mt-3">
              <span className="badge bg-gray-100 text-gray-700">{t.tone}</span>
              <span className="badge bg-gray-100 text-gray-700">{t.category}</span>
            </div>
            <details className="mt-3">
              <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">Structure instructions</summary>
              <p className="text-sm text-gray-600 mt-2 bg-gray-50 p-3 rounded">{t.structure_prompt}</p>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
