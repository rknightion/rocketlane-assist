import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { configApi, usersApi, User } from '../services/api';

interface OnboardingWizardProps {
  onComplete: () => void;
}

interface WizardStep {
  title: string;
  description: string;
  component: React.ComponentType<{
    onNext: () => void;
    formData: FormData;
    setFormData: (data: FormData) => void;
  }>;
}

interface FormData {
  llm_provider: 'openai' | 'anthropic';
  llm_model: string;
  custom_model: string;
  use_custom_model: boolean;
  openai_api_key: string;
  anthropic_api_key: string;
  rocketlane_api_key: string;
  rocketlane_user_id: string;
}

// Step 1: Welcome
const WelcomeStep: React.FC<{ onNext: () => void }> = ({ onNext }) => (
  <div className="wizard-step">
    <h2>Welcome to Rocketlane Assist! 🚀</h2>
    <p>
      This AI-powered assistant helps you manage your Rocketlane projects more efficiently
      by providing intelligent summaries, insights, and automation.
    </p>
    <h3>What you&apos;ll need:</h3>
    <ul>
      <li>✓ Your Rocketlane API key</li>
      <li>✓ An OpenAI or Anthropic API key</li>
      <li>✓ About 2 minutes to complete setup</li>
    </ul>
    <button onClick={onNext} className="wizard-button wizard-button-primary">
      Let&apos;s Get Started
    </button>
  </div>
);

// Step 2: Rocketlane API Key
const RocketlaneStep: React.FC<{
  onNext: () => void;
  formData: FormData;
  setFormData: (data: FormData) => void;
}> = ({ onNext, formData, setFormData }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const testConnection = async () => {
    if (!formData.rocketlane_api_key) return;

    setTesting(true);
    setTestResult(null);

    try {
      // Save the key temporarily to test it
      await configApi.updateConfig({
        llm_provider: formData.llm_provider,
        llm_model: formData.llm_model || 'gpt-4',
        rocketlane_api_key: formData.rocketlane_api_key
      });

      // Use dedicated test endpoint for quick validation
      const response = await fetch('/api/v1/test/rocketlane', {
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        setTestResult('success');
      } else {
        setTestResult('error');
      }
    } catch (_error) {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="wizard-step">
      <h2>Connect to Rocketlane</h2>
      <p>First, let&apos;s connect to your Rocketlane account.</p>

      <div className="form-group">
        <label htmlFor="rocketlane_api_key">Rocketlane API Key</label>
        <input
          type="password"
          id="rocketlane_api_key"
          value={formData.rocketlane_api_key}
          onChange={(e) => setFormData({ ...formData, rocketlane_api_key: e.target.value })}
          placeholder="Enter your Rocketlane API key"
        />
        <small>You can find this in Rocketlane Settings → API Keys</small>
      </div>

      <button
        onClick={testConnection}
        disabled={!formData.rocketlane_api_key || testing}
        className="wizard-button wizard-button-secondary"
      >
        {testing ? 'Testing Connection...' : 'Test Connection'}
      </button>

      {testResult === 'success' && (
        <div className="message message-success">
          ✓ Successfully connected to Rocketlane!
        </div>
      )}

      {testResult === 'error' && (
        <div className="message message-error">
          ✗ Could not connect. Please check your API key.
        </div>
      )}

      <button
        onClick={onNext}
        disabled={!formData.rocketlane_api_key || testResult !== 'success'}
        className="wizard-button wizard-button-primary"
      >
        Next: Select User
      </button>
    </div>
  );
};

// Step 3: User Selection
const UserSelectionStep: React.FC<{
  onNext: () => void;
  formData: FormData;
  setFormData: (data: FormData) => void;
}> = ({ onNext, formData, setFormData }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const userList = await usersApi.getUsers();
      setUsers(userList);
    } catch (_err) {
      setError('Failed to load users. Please check your Rocketlane API key.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wizard-step">
      <h2>Select Your User Account</h2>
      <p>Choose which user account to use for filtering tasks and projects.</p>

      {loading && (
        <div className="loading">Loading users...</div>
      )}

      {error && (
        <div className="message message-error">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="form-group">
          <label htmlFor="rocketlane_user_id">User Account</label>
          <select
            id="rocketlane_user_id"
            value={formData.rocketlane_user_id}
            onChange={(e) => setFormData({ ...formData, rocketlane_user_id: e.target.value })}
          >
            <option value="">All tasks (no filter)</option>
            {users.map(user => (
              <option key={user.userId} value={user.userId}>
                {user.fullName || `${user.firstName} ${user.lastName}`.trim() || user.emailId}
              </option>
            ))}
          </select>
          <small>
            Select your user account to see only tasks assigned to you.
            Leave empty to see all tasks across the organization.
          </small>
        </div>
      )}

      <button
        onClick={onNext}
        disabled={loading}
        className="wizard-button wizard-button-primary"
      >
        Next: Choose AI Provider
      </button>
    </div>
  );
};

// Step 4: LLM Provider Selection
const LLMProviderStep: React.FC<{
  onNext: () => void;
  formData: FormData;
  setFormData: (data: FormData) => void;
}> = ({ onNext, formData, setFormData }) => {
  const openaiModels = [
    { value: 'gpt-4.1', label: 'GPT-4.1' },
    { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
    { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  ];

  const anthropicModels = [
    { value: 'claude-opus-4-0', label: 'Claude Opus 4' },
    { value: 'claude-sonnet-4-0', label: 'Claude Sonnet 4' },
    { value: 'claude-3-7-sonnet-latest', label: 'Claude Sonnet 3.7' },
    { value: 'claude-3-5-sonnet-latest', label: 'Claude Sonnet 3.5' },
    { value: 'claude-3-5-haiku-latest', label: 'Claude Haiku 3.5' },
  ];

  const models = formData.llm_provider === 'openai' ? openaiModels : anthropicModels;

  return (
    <div className="wizard-step">
      <h2>Choose Your AI Provider</h2>
      <p>Select which AI provider you&apos;d like to use for generating insights.</p>

      <div className="form-group">
        <label>AI Provider</label>
        <div className="provider-selector">
          <button
            className={`provider-button ${formData.llm_provider === 'openai' ? 'active' : ''}`}
            onClick={() => setFormData({ ...formData, llm_provider: 'openai', llm_model: '', use_custom_model: false })}
          >
            <h3>OpenAI</h3>
            <p>GPT-4 and GPT-3.5 models</p>
          </button>
          <button
            className={`provider-button ${formData.llm_provider === 'anthropic' ? 'active' : ''}`}
            onClick={() => setFormData({ ...formData, llm_provider: 'anthropic', llm_model: '', use_custom_model: false })}
          >
            <h3>Anthropic</h3>
            <p>Claude 3 models</p>
          </button>
        </div>
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
          {models.map(model => (
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

      <button
        onClick={onNext}
        disabled={!formData.llm_model && !formData.custom_model}
        className="wizard-button wizard-button-primary"
      >
        Next: Add API Key
      </button>
    </div>
  );
};

// Step 5: API Key Configuration
const APIKeyStep: React.FC<{
  onNext: () => void;
  formData: FormData;
  setFormData: (data: FormData) => void;
}> = ({ onNext, formData, setFormData }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const apiKeyField = formData.llm_provider === 'openai' ? 'openai_api_key' : 'anthropic_api_key';
  const apiKeyValue = formData[apiKeyField];

  const testConnection = async () => {
    if (!apiKeyValue) return;

    setTesting(true);
    setTestResult(null);

    try {
      const updateData: any = {
        llm_provider: formData.llm_provider,
        llm_model: formData.use_custom_model ? formData.custom_model : formData.llm_model,
        rocketlane_api_key: formData.rocketlane_api_key,
        rocketlane_user_id: formData.rocketlane_user_id,
      };
      updateData[apiKeyField] = apiKeyValue;

      await configApi.updateConfig(updateData);

      // Use dedicated LLM test endpoint
      const testResponse = await fetch('/api/v1/test/llm', {
        headers: { 'Accept': 'application/json' }
      });

      if (testResponse.ok) {
        setTestResult('success');
      } else {
        setTestResult('error');
      }
    } catch (_error) {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="wizard-step">
      <h2>Add {formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'} API Key</h2>
      <p>
        Finally, add your {formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'} API key
        to enable AI-powered features.
      </p>

      <div className="form-group">
        <label htmlFor={apiKeyField}>
          {formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'} API Key
        </label>
        <input
          type="password"
          id={apiKeyField}
          value={apiKeyValue}
          onChange={(e) => setFormData({ ...formData, [apiKeyField]: e.target.value })}
          placeholder={`Enter your ${formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'} API key`}
        />
        <small>
          {formData.llm_provider === 'openai'
            ? 'Get your key from platform.openai.com'
            : 'Get your key from console.anthropic.com'}
        </small>
      </div>

      <button
        onClick={testConnection}
        disabled={!apiKeyValue || testing}
        className="wizard-button wizard-button-secondary"
      >
        {testing ? 'Testing Connection...' : 'Test Connection'}
      </button>

      {testResult === 'success' && (
        <div className="message message-success">
          ✓ Successfully connected to {formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'}!
        </div>
      )}

      {testResult === 'error' && (
        <div className="message message-error">
          ✗ Could not connect. Please check your API key.
        </div>
      )}

      <button
        onClick={onNext}
        disabled={!apiKeyValue || testResult !== 'success'}
        className="wizard-button wizard-button-primary"
      >
        Complete Setup
      </button>
    </div>
  );
};

// Step 6: Complete
const CompleteStep: React.FC<{ onNext: () => void }> = ({ onNext }) => (
  <div className="wizard-step wizard-step-complete">
    <div className="success-icon">🎉</div>
    <h2>Setup Complete!</h2>
    <p>
      You&apos;re all set! Rocketlane Assist is now configured and ready to help you
      manage your projects more efficiently.
    </p>
    <h3>What&apos;s Next?</h3>
    <ul>
      <li>Browse your projects and view AI-generated summaries</li>
      <li>Explore task insights and recommendations</li>
      <li>Customize settings anytime from the Settings page</li>
    </ul>
    <button onClick={onNext} className="wizard-button wizard-button-primary">
      Go to Projects
    </button>
  </div>
);

function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({
    llm_provider: 'openai',
    llm_model: '',
    custom_model: '',
    use_custom_model: false,
    openai_api_key: '',
    anthropic_api_key: '',
    rocketlane_api_key: '',
    rocketlane_user_id: '',
  });

  const steps: WizardStep[] = [
    {
      title: 'Welcome',
      description: 'Get started with Rocketlane Assist',
      component: WelcomeStep
    },
    {
      title: 'Rocketlane',
      description: 'Connect your Rocketlane account',
      component: RocketlaneStep
    },
    {
      title: 'User',
      description: 'Select your user account',
      component: UserSelectionStep
    },
    {
      title: 'AI Provider',
      description: 'Choose your AI provider',
      component: LLMProviderStep
    },
    {
      title: 'API Key',
      description: 'Add your AI provider API key',
      component: APIKeyStep
    },
    {
      title: 'Complete',
      description: 'Setup complete!',
      component: CompleteStep
    },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
      navigate('/');
    }
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="onboarding-wizard">
      <div className="wizard-progress">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`progress-step ${index <= currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
          >
            <div className="progress-dot">{index < currentStep ? '✓' : index + 1}</div>
            <span className="progress-label">{step.title}</span>
          </div>
        ))}
      </div>

      <div className="wizard-content">
        <CurrentStepComponent
          onNext={handleNext}
          formData={formData}
          setFormData={setFormData}
        />
      </div>
    </div>
  );
}

export default OnboardingWizard;
