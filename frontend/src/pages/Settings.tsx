import { useState, useEffect } from 'react';
import { configApi, Config } from '../services/api';

interface SettingsProps {
  onConfigUpdate: () => void;
}

function Settings({ onConfigUpdate }: SettingsProps) {
  const [config, setConfig] = useState<Config | null>(null);
  const [formData, setFormData] = useState({
    llm_provider: 'openai' as 'openai' | 'anthropic',
    llm_model: '',
    openai_api_key: '',
    anthropic_api_key: '',
    rocketlane_api_key: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const currentConfig = await configApi.getConfig();
      setConfig(currentConfig);
      setFormData(prev => ({
        ...prev,
        llm_provider: currentConfig.llm_provider,
        llm_model: currentConfig.llm_model,
      }));
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setMessage(null);
      
      const updateData: any = {
        llm_provider: formData.llm_provider,
        llm_model: formData.llm_model,
      };

      // Only include API keys if they were changed
      if (formData.openai_api_key) updateData.openai_api_key = formData.openai_api_key;
      if (formData.anthropic_api_key) updateData.anthropic_api_key = formData.anthropic_api_key;
      if (formData.rocketlane_api_key) updateData.rocketlane_api_key = formData.rocketlane_api_key;

      await configApi.updateConfig(updateData);
      setMessage({ type: 'success', text: 'Configuration updated successfully. Please restart the application.' });
      onConfigUpdate();
      
      // Clear sensitive fields
      setFormData(prev => ({
        ...prev,
        openai_api_key: '',
        anthropic_api_key: '',
        rocketlane_api_key: '',
      }));
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update configuration.' });
      console.error('Error updating config:', error);
    } finally {
      setSaving(false);
    }
  };

  const getModelOptions = () => {
    if (formData.llm_provider === 'openai') {
      return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'];
    } else {
      return ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'];
    }
  };

  return (
    <div className="settings">
      <h2>Settings</h2>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="settings-form">
        <div className="form-section">
          <h3>LLM Configuration</h3>
          
          <div className="form-group">
            <label htmlFor="llm_provider">LLM Provider</label>
            <select
              id="llm_provider"
              value={formData.llm_provider}
              onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value as 'openai' | 'anthropic' })}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="llm_model">Model</label>
            <select
              id="llm_model"
              value={formData.llm_model}
              onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
            >
              {getModelOptions().map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-section">
          <h3>API Keys</h3>
          
          <div className="form-group">
            <label htmlFor="openai_api_key">
              OpenAI API Key {config?.has_openai_key && <span className="configured">✓ Configured</span>}
            </label>
            <input
              type="password"
              id="openai_api_key"
              value={formData.openai_api_key}
              onChange={(e) => setFormData({ ...formData, openai_api_key: e.target.value })}
              placeholder={config?.has_openai_key ? 'Enter new key to update' : 'Enter your OpenAI API key'}
            />
          </div>

          <div className="form-group">
            <label htmlFor="anthropic_api_key">
              Anthropic API Key {config?.has_anthropic_key && <span className="configured">✓ Configured</span>}
            </label>
            <input
              type="password"
              id="anthropic_api_key"
              value={formData.anthropic_api_key}
              onChange={(e) => setFormData({ ...formData, anthropic_api_key: e.target.value })}
              placeholder={config?.has_anthropic_key ? 'Enter new key to update' : 'Enter your Anthropic API key'}
            />
          </div>

          <div className="form-group">
            <label htmlFor="rocketlane_api_key">
              Rocketlane API Key {config?.has_rocketlane_key && <span className="configured">✓ Configured</span>}
            </label>
            <input
              type="password"
              id="rocketlane_api_key"
              value={formData.rocketlane_api_key}
              onChange={(e) => setFormData({ ...formData, rocketlane_api_key: e.target.value })}
              placeholder={config?.has_rocketlane_key ? 'Enter new key to update' : 'Enter your Rocketlane API key'}
            />
          </div>
        </div>

        <button type="submit" disabled={saving} className="save-button">
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
}

export default Settings;