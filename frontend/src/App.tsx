import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import Settings from './pages/Settings';
import { configApi } from './services/api';
import './App.css';

function App() {
  const [hasApiKeys, setHasApiKeys] = useState(false);

  useEffect(() => {
    checkConfiguration();
  }, []);

  const checkConfiguration = async () => {
    try {
      const config = await configApi.getConfig();
      setHasApiKeys(config.has_rocketlane_key && (config.has_openai_key || config.has_anthropic_key));
    } catch (error) {
      console.error('Failed to check configuration:', error);
    }
  };

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Rocketlane Assist</h1>
          <nav>
            <Link to="/">Projects</Link>
            <Link to="/settings">Settings</Link>
          </nav>
        </header>

        {!hasApiKeys && (
          <div className="warning-banner">
            ⚠️ Please configure your API keys in <Link to="/settings">Settings</Link> to get started.
          </div>
        )}

        <main className="app-main">
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/settings" element={<Settings onConfigUpdate={checkConfiguration} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;