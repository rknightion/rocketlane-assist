import { useState, useEffect } from 'react';
import { configApi, Config, usersApi, User, googleCalendarApi, GoogleCalendarStatus } from '../services/api';
import { setUser, clearUser } from '../lib/observability';

interface SettingsProps {
  onConfigUpdate: () => void;
}

function Settings({ onConfigUpdate }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<'rocketlane' | 'llm' | 'integrations'>('rocketlane');
  const [config, setConfig] = useState<Config | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [googleCalendarStatus, setGoogleCalendarStatus] = useState<GoogleCalendarStatus | null>(null);
  const [loadingGoogleCalendar, setLoadingGoogleCalendar] = useState(false);
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
    loadGoogleCalendarStatus();
  }, []);

  useEffect(() => {
    // Load users when Rocketlane API key is configured
    if (config?.has_rocketlane_key) {
      loadUsers();
    }
  }, [config?.has_rocketlane_key]);

  useEffect(() => {
    // Set user tracking when users are loaded and we have a selected user
    if (config?.rocketlane_user_id && users.length > 0) {
      const selectedUser = users.find(u => u.userId === config.rocketlane_user_id);
      if (selectedUser) {
        setUser(selectedUser.userId, selectedUser.emailId, selectedUser.fullName || selectedUser.firstName);
      }
    }
  }, [config?.rocketlane_user_id, users]);
  
  useEffect(() => {
    // Check for OAuth callback parameters
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('gcal_connected') === 'true') {
      setMessage({ type: 'success', text: 'Google Calendar connected successfully!' });
      setActiveTab('integrations');
      loadGoogleCalendarStatus();
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('gcal_error') === 'true') {
      setMessage({ type: 'error', text: 'Failed to connect Google Calendar. Please try again.' });
      setActiveTab('integrations');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

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
  
  const loadGoogleCalendarStatus = async () => {
    try {
      setLoadingGoogleCalendar(true);
      const status = await googleCalendarApi.getStatus();
      setGoogleCalendarStatus(status);
    } catch (error) {
      console.error('Failed to load Google Calendar status:', error);
    } finally {
      setLoadingGoogleCalendar(false);
    }
  };
  
  const handleGoogleCalendarConnect = async () => {
    try {
      const { auth_url } = await googleCalendarApi.getAuthUrl();
      window.location.href = auth_url;
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to start Google Calendar authorization' });
    }
  };
  
  const handleGoogleCalendarSync = async () => {
    try {
      const result = await googleCalendarApi.sync();
      setMessage({ type: 'success', text: `Synced ${result.event_count} events from Google Calendar` });
      await loadGoogleCalendarStatus();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to sync Google Calendar events' });
    }
  };
  
  const handleGoogleCalendarDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Google Calendar?')) {
      return;
    }
    try {
      await googleCalendarApi.disconnect();
      setMessage({ type: 'success', text: 'Google Calendar disconnected successfully' });
      await loadGoogleCalendarStatus();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to disconnect Google Calendar' });
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

      // Update Faro user tracking if user was changed
      if (updateData.rocketlane_user_id !== undefined) {
        if (updateData.rocketlane_user_id) {
          const selectedUser = users.find(u => u.userId === updateData.rocketlane_user_id);
          if (selectedUser) {
            setUser(selectedUser.userId, selectedUser.emailId, selectedUser.fullName || selectedUser.firstName);
          }
        } else {
          clearUser();
        }
      }

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

      <div className="settings-tabs">
        <button
          className={`tab-button ${activeTab === 'rocketlane' ? 'active' : ''}`}
          onClick={() => setActiveTab('rocketlane')}
        >
          Rocketlane
        </button>
        <button
          className={`tab-button ${activeTab === 'llm' ? 'active' : ''}`}
          onClick={() => setActiveTab('llm')}
        >
          LLM Settings
        </button>
        <button
          className={`tab-button ${activeTab === 'integrations' ? 'active' : ''}`}
          onClick={() => setActiveTab('integrations')}
        >
          Integrations
        </button>
      </div>

      <form onSubmit={handleSubmit} className="settings-form">
        {activeTab === 'rocketlane' && (
          <div className="form-section">
            <h3>Rocketlane Configuration</h3>

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
        )}

        {activeTab === 'llm' && (
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
          </div>
        )}

        {activeTab === 'integrations' && (
          <div className="form-section">
            <h3>Google Calendar Integration</h3>
            
            {loadingGoogleCalendar ? (
              <div>Loading Google Calendar status...</div>
            ) : (
              <>
                <div className="form-group">
                  <p className="integration-status">
                    Status: {' '}
                    {googleCalendarStatus?.is_authenticated ? (
                      <span className="configured">✓ Connected</span>
                    ) : googleCalendarStatus?.is_configured ? (
                      <span className="not-configured">Not Connected</span>
                    ) : (
                      <span className="not-configured">Not Configured</span>
                    )}
                  </p>
                  
                  {googleCalendarStatus?.is_authenticated && googleCalendarStatus.user_email && (
                    <p className="help-text">
                      Connected as: <strong>{googleCalendarStatus.user_email}</strong>
                    </p>
                  )}
                  
                  {!googleCalendarStatus?.is_authenticated && (
                    <p className="help-text">
                      Google Calendar integration allows syncing your calendar events with task timelines.
                    </p>
                  )}
                  
                  {!googleCalendarStatus?.is_authenticated ? (
                    <button 
                      type="button" 
                      className="oauth-button" 
                      onClick={handleGoogleCalendarConnect}
                      disabled={!googleCalendarStatus?.is_configured}
                    >
                      {googleCalendarStatus?.is_configured 
                        ? 'Connect Google Calendar' 
                        : 'Google Calendar Not Configured (Set environment variables)'}
                    </button>
                  ) : (
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                      <button 
                        type="button" 
                        className="oauth-button"
                        onClick={handleGoogleCalendarSync}
                      >
                        Sync Events
                      </button>
                      <button 
                        type="button" 
                        className="oauth-button disconnect"
                        onClick={handleGoogleCalendarDisconnect}
                        style={{ backgroundColor: '#ff4444' }}
                      >
                        Disconnect
                      </button>
                    </div>
                  )}
                </div>

                {googleCalendarStatus?.is_authenticated && (
                  <div className="form-group">
                    <label>Cached Events</label>
                    <p className="event-count">
                      {googleCalendarStatus.event_count > 0 
                        ? `${googleCalendarStatus.event_count} events synced` 
                        : 'No events synced yet'}
                    </p>
                    {googleCalendarStatus.last_synced && (
                      <p className="help-text">
                        Last synced: {new Date(googleCalendarStatus.last_synced).toLocaleString()}
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        <button type="submit" disabled={saving} className="save-button">
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
}

export default Settings;
