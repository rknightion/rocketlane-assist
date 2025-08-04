import { useState, useEffect } from 'react';
import { configApi, Config, usersApi, User } from '../services/api';

interface SettingsProps {
  onConfigUpdate: () => void;
}

function Settings({ onConfigUpdate }: SettingsProps) {
  const [config, setConfig] = useState<Config | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [formData, setFormData] = useState({
    llm_provider: 'openai' as 'openai' | 'anthropic',
    llm_model: '',
    custom_model: '',
    use_custom_model: false,
    openai_api_key: '',
    anthropic_api_key: '',
    rocketlane_api_key: '',
    rocketlane_user_id: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  useEffect(() => {
    // Load users when Rocketlane API key is configured
    if (config?.has_rocketlane_key) {
      loadUsers();
    }
  }, [config?.has_rocketlane_key]);

  const loadConfig = async () => {
    try {
      const currentConfig = await configApi.getConfig();
      setConfig(currentConfig);

      // Check if the current model is in our predefined list
      const modelOptions = currentConfig.llm_provider === 'openai'
        ? ['gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4o', 'gpt-4o-mini']
        : ['claude-opus-4-0', 'claude-sonnet-4-0', 'claude-3-7-sonnet-latest', 'claude-3-5-sonnet-latest', 'claude-3-5-haiku-latest'];

      const isCustomModel = !modelOptions.includes(currentConfig.llm_model);

      setFormData(prev => ({
        ...prev,
        llm_provider: currentConfig.llm_provider,
        llm_model: isCustomModel ? '' : currentConfig.llm_model,
        custom_model: isCustomModel ? currentConfig.llm_model : '',
        use_custom_model: isCustomModel,
        rocketlane_user_id: currentConfig.rocketlane_user_id || '',
      }));
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const userList = await usersApi.getUsers();
      setUsers(userList);
    } catch (error) {
      console.error('Failed to load users:', error);
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setMessage(null);

      const updateData: any = {
        llm_provider: formData.llm_provider,
        llm_model: formData.use_custom_model ? formData.custom_model : formData.llm_model,
      };

      // Only include API keys if they were changed
      if (formData.openai_api_key) updateData.openai_api_key = formData.openai_api_key;
      if (formData.anthropic_api_key) updateData.anthropic_api_key = formData.anthropic_api_key;
      if (formData.rocketlane_api_key) updateData.rocketlane_api_key = formData.rocketlane_api_key;
      if (formData.rocketlane_user_id !== config?.rocketlane_user_id) {
        updateData.rocketlane_user_id = formData.rocketlane_user_id;
      }

      await configApi.updateConfig(updateData);
      setMessage({ type: 'success', text: 'Configuration updated successfully.' });
      
      // Clear sensitive fields
      setFormData(prev => ({
        ...prev,
        openai_api_key: '',
        anthropic_api_key: '',
        rocketlane_api_key: '',
      }));

      // Reload config to get updated state and trigger user loading
      await loadConfig();
      onConfigUpdate();
    } catch (error: any) {
      // Check if it's an API key validation error
      if (error.response?.data?.detail?.includes('Invalid Rocketlane API key')) {
        setMessage({ type: 'error', text: error.response.data.detail });
        // Reload config to clear invalid key from UI
        await loadConfig();
      } else {
        setMessage({ type: 'error', text: 'Failed to update configuration.' });
      }
      console.error('Error updating config:', error);
    } finally {
      setSaving(false);
    }
  };

  const getModelOptions = () => {
    if (formData.llm_provider === 'openai') {
      return [
        { value: 'gpt-4.1', label: 'GPT-4.1' },
        { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
        { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano' },
        { value: 'gpt-4o', label: 'GPT-4o' },
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
      ];
    } else {
      return [
        { value: 'claude-opus-4-0', label: 'Claude Opus 4' },
        { value: 'claude-sonnet-4-0', label: 'Claude Sonnet 4' },
        { value: 'claude-3-7-sonnet-latest', label: 'Claude Sonnet 3.7' },
        { value: 'claude-3-5-sonnet-latest', label: 'Claude Sonnet 3.5' },
        { value: 'claude-3-5-haiku-latest', label: 'Claude Haiku 3.5' },
      ];
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
              value={formData.use_custom_model ? 'custom' : formData.llm_model}
              onChange={(e) => {
                if (e.target.value === 'custom') {
                  setFormData({ ...formData, use_custom_model: true });
                } else {
                  setFormData({ ...formData, llm_model: e.target.value, use_custom_model: false });
                }
              }}
            >
              <option value="">Select a model</option>
              {getModelOptions().map(model => (
                <option key={model.value} value={model.value}>{model.label}</option>
              ))}
              <option value="custom">Custom Model</option>
            </select>
          </div>

          {formData.use_custom_model && (
            <div className="form-group">
              <label htmlFor="custom_model">Custom Model ID</label>
              <input
                type="text"
                id="custom_model"
                value={formData.custom_model}
                onChange={(e) => setFormData({ ...formData, custom_model: e.target.value })}
                placeholder="Enter custom model ID"
              />
            </div>
          )}
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

          {config?.has_rocketlane_key && (
            <div className="form-group">
              <label htmlFor="rocketlane_user_id">
                Rocketlane User Filter
                {loadingUsers && <span className="loading-text"> (Loading users...)</span>}
              </label>
              <select
                id="rocketlane_user_id"
                value={formData.rocketlane_user_id}
                onChange={(e) => setFormData({ ...formData, rocketlane_user_id: e.target.value })}
                disabled={loadingUsers}
              >
                <option value="">⚠️ Select a user (required)</option>
                {users.map(user => (
                  <option key={user.userId} value={user.userId}>
                    {user.fullName || `${user.firstName} ${user.lastName}`.trim() || user.emailId}
                  </option>
                ))}
              </select>
              <small className="help-text">
                <strong>Required:</strong> You must select a user. All operations will be blocked until a user is selected.
              </small>
            </div>
          )}
        </div>

        <button type="submit" disabled={saving} className="save-button">
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
}

export default Settings;
