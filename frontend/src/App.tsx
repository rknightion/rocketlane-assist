import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom';
import { FaroErrorBoundary } from '@grafana/faro-react';
import Home from './pages/Home';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import Timesheets from './pages/Timesheets';
import Settings from './pages/Settings';
import OnboardingWizard from './components/OnboardingWizard';
import { configApi } from './services/api';
import { initializeObservability } from './lib/observability';
import './App.css';

function App() {
  const [hasApiKeys, setHasApiKeys] = useState(false);
  const [hasUserSelected, setHasUserSelected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    // Initialize observability
    initializeObservability();

    checkConfiguration();
  }, []);

  const checkConfiguration = async () => {
    try {
      const config = await configApi.getConfig();
      const configured = config.has_rocketlane_key && (config.has_openai_key || config.has_anthropic_key);
      const userSelected = config.rocketlane_user_id ? true : false;

      setHasApiKeys(configured);
      setHasUserSelected(userSelected);

      // Show onboarding if not configured and hasn't been dismissed
      const onboardingDismissed = localStorage.getItem('onboardingDismissed') === 'true';
      setShowOnboarding(!configured && !onboardingDismissed);
    } catch (error) {
      console.error('Failed to check configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const completeOnboarding = () => {
    localStorage.setItem('onboardingDismissed', 'true');
    setShowOnboarding(false);
    checkConfiguration();
  };

  if (loading) {
    return <div className="app-loading">Loading...</div>;
  }

  return (
    <FaroErrorBoundary>
      <Router>
        <div className="app">
        {showOnboarding ? (
          <Routes>
            <Route path="*" element={<OnboardingWizard onComplete={completeOnboarding} />} />
          </Routes>
        ) : (
          <>
            <header className="app-header">
              <h1>Rocketlane Assist</h1>
              <nav>
                <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
                  Home
                </NavLink>
                <NavLink to="/projects" className={({ isActive }) => isActive ? 'active' : ''}>
                  Projects
                </NavLink>
                <NavLink to="/timesheets" className={({ isActive }) => isActive ? 'active' : ''}>
                  Timesheets
                </NavLink>
                <NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>
                  Settings
                </NavLink>
              </nav>
            </header>

            {!hasApiKeys && (
              <div className="warning-banner">
                ⚠️ Please configure your API keys in <Link to="/settings">Settings</Link> to get started.
                {' '}
                <button
                  onClick={() => setShowOnboarding(true)}
                  style={{
                    background: 'none',
                    border: '1px solid white',
                    color: 'white',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginLeft: '1rem'
                  }}
                >
                  Run Setup Wizard
                </button>
              </div>
            )}

            {hasApiKeys && !hasUserSelected && (
              <div className="warning-banner" style={{ backgroundColor: '#ff9800' }}>
                ⚠️ Please select your user account in <Link to="/settings">Settings</Link> to continue.
                All operations require user context for proper filtering.
              </div>
            )}

            <main className="app-main">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/:projectId" element={<ProjectDetail />} />
                <Route path="/timesheets" element={<Timesheets />} />
                <Route path="/settings" element={<Settings onConfigUpdate={checkConfiguration} />} />
              </Routes>
            </main>
          </>
        )}
      </div>
    </Router>
    </FaroErrorBoundary>
  );
}

export default App;
