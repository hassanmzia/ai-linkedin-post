import { useEffect, useState } from 'react';
import { configAPI } from '../services/api';
import type { APIConfig } from '../types';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [config, setConfig] = useState<APIConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    openai_api_key: '',
    openai_base_url: '',
    openai_model: 'gpt-4o-mini',
    openai_eval_model: 'gpt-4o',
    tavily_api_key: '',
  });

  useEffect(() => {
    configAPI.get().then(({ data }) => {
      setConfig(data);
      setForm({
        openai_api_key: '',
        openai_base_url: data.openai_base_url || '',
        openai_model: data.openai_model || 'gpt-4o-mini',
        openai_eval_model: data.openai_eval_model || 'gpt-4o',
        tavily_api_key: '',
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: Record<string, string> = {
        openai_base_url: form.openai_base_url,
        openai_model: form.openai_model,
        openai_eval_model: form.openai_eval_model,
      };
      if (form.openai_api_key) payload.openai_api_key = form.openai_api_key;
      if (form.tavily_api_key) payload.tavily_api_key = form.tavily_api_key;

      const { data } = await configAPI.update(payload);
      setConfig(data);
      setForm((prev) => ({ ...prev, openai_api_key: '', tavily_api_key: '' }));
      toast.success('Settings saved');
    } catch (err: any) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Configure your API keys and preferences</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* API Keys */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">API Keys</h2>
          <p className="text-sm text-gray-500">Your API keys are stored securely and never displayed after saving.</p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              OpenAI API Key
              {config?.has_openai_key && (
                <span className="ml-2 badge bg-green-100 text-green-700">Configured</span>
              )}
            </label>
            <input type="password" value={form.openai_api_key}
              onChange={(e) => setForm({ ...form, openai_api_key: e.target.value })}
              className="input-field" placeholder={config?.has_openai_key ? 'Leave blank to keep current key' : 'sk-...'} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tavily API Key (for web research)
              {config?.has_tavily_key && (
                <span className="ml-2 badge bg-green-100 text-green-700">Configured</span>
              )}
            </label>
            <input type="password" value={form.tavily_api_key}
              onChange={(e) => setForm({ ...form, tavily_api_key: e.target.value })}
              className="input-field" placeholder={config?.has_tavily_key ? 'Leave blank to keep current key' : 'tvly-...'} />
          </div>
        </div>

        {/* Model Configuration */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Model Configuration</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">OpenAI Base URL (optional)</label>
            <input type="text" value={form.openai_base_url}
              onChange={(e) => setForm({ ...form, openai_base_url: e.target.value })}
              className="input-field" placeholder="Leave blank for default OpenAI endpoint" />
            <p className="text-xs text-gray-400 mt-1">Use this for custom endpoints or compatible APIs</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Primary Model</label>
              <select value={form.openai_model} onChange={(e) => setForm({ ...form, openai_model: e.target.value })}
                className="input-field">
                <option value="gpt-4o-mini">gpt-4o-mini (Fast, Cost-effective)</option>
                <option value="gpt-4o">gpt-4o (Powerful)</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo (Budget)</option>
              </select>
              <p className="text-xs text-gray-400 mt-1">Used by Supervisor, Researcher, Writer, and Critic agents</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Evaluation Model</label>
              <select value={form.openai_eval_model} onChange={(e) => setForm({ ...form, openai_eval_model: e.target.value })}
                className="input-field">
                <option value="gpt-4o">gpt-4o (Recommended)</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
              </select>
              <p className="text-xs text-gray-400 mt-1">Used for groundedness evaluation (more powerful model recommended)</p>
            </div>
          </div>
        </div>

        {/* Multi-Agent System Info */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Agent Architecture</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: 'Supervisor', desc: 'Orchestrates workflow, routes to agents using deterministic logic with LLM fallback', color: 'bg-indigo-100 text-indigo-700' },
              { name: 'Researcher', desc: 'Searches web via Tavily API, summarizes findings into bullet points', color: 'bg-emerald-100 text-emerald-700' },
              { name: 'Writer', desc: 'Creates and revises LinkedIn posts based on research and feedback', color: 'bg-blue-100 text-blue-700' },
              { name: 'Critic', desc: 'Evaluates drafts on hook, clarity, value, structure, engagement, tone', color: 'bg-amber-100 text-amber-700' },
              { name: 'Evaluator', desc: 'Checks groundedness of claims against research (score 0-5)', color: 'bg-purple-100 text-purple-700' },
            ].map((agent) => (
              <div key={agent.name} className="p-3 rounded-lg bg-gray-50">
                <span className={`badge ${agent.color} mb-2`}>{agent.name}</span>
                <p className="text-sm text-gray-600">{agent.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Protocol Info */}
        <div className="card space-y-3">
          <h2 className="text-lg font-semibold">Protocol Endpoints</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-gray-700">MCP Manifest</span>
              <code className="text-xs text-gray-500">/mcp/manifest/</code>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-gray-700">MCP Tools</span>
              <code className="text-xs text-gray-500">/mcp/tools/list/</code>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-gray-700">A2A Agents</span>
              <code className="text-xs text-gray-500">/a2a/agents/</code>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-gray-700">A2A Discovery</span>
              <code className="text-xs text-gray-500">/.well-known/agent.json</code>
            </div>
            <div className="flex justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-gray-700">WebSocket</span>
              <code className="text-xs text-gray-500">ws://172.168.1.95:4052/ws</code>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}
