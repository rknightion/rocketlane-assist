import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { statisticsApi } from '../services/api';
import './Home.css';

interface UserStatistics {
  user?: {
    userId?: string;
    fullName?: string;
    emailId?: string;
  };
  statistics?: {
    total_tasks?: number;
    active_tasks?: number;
    completed_tasks?: number;
    overdue_tasks?: number;
    at_risk_tasks?: number;
    due_this_week?: number;
    hours_logged_this_week?: number;
    projects_count?: number;
  };
  tasks?: {
    active?: Array<any>;
    at_risk?: Array<any>;
    due_this_week?: Array<any>;
    overdue?: Array<any>;
  };
  cache_status?: 'fresh' | 'stale' | 'updating' | 'error' | 'refreshed';
  last_updated?: string;
}

const Home = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);

  useEffect(() => {
    loadStatistics();
    // Set up auto-refresh every 30 seconds for updating status
    const interval = setInterval(() => {
      loadStatistics(false);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStatistics = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const data = await statisticsApi.getUserStatistics();
      setStatistics(data);
    } catch (err) {
      console.error('Failed to load statistics:', err);
      if (err instanceof Error) {
        if (err.message.includes('403')) {
          setError('Please select your user account in Settings to view statistics.');
        } else {
          setError(err.message || 'Failed to load statistics');
        }
      } else {
        setError('Failed to load statistics');
      }
    } finally {
      setLoading(false);
    }
  };


  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatLastUpdated = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return date.toLocaleString();
  };

  const getCacheStatusDisplay = () => {
    if (!statistics?.cache_status) return null;
    
    const status = statistics.cache_status;
    let statusClass = '';
    let statusText = '';
    let statusIcon = '';
    
    switch (status) {
      case 'fresh':
        statusClass = 'cache-fresh';
        statusText = 'Data is up to date';
        statusIcon = '✓';
        break;
      case 'stale':
        statusClass = 'cache-stale';
        statusText = 'Data may be outdated';
        statusIcon = '⟳';
        break;
      case 'updating':
        statusClass = 'cache-updating';
        statusText = 'Fetching latest data...';
        statusIcon = '⟳';
        break;
      case 'error':
        statusClass = 'cache-error';
        statusText = 'Error loading data';
        statusIcon = '⚠';
        break;
    }
    
    return {
      class: statusClass,
      text: statusText,
      icon: statusIcon
    };
  };

  // Handle initial loading state (first time cache population)
  if (loading && !statistics) {
    return (
      <div className="home-page">
        <div className="cache-initializing">
          <div className="cache-icon">⏳</div>
          <h2>Initializing Dashboard</h2>
          <p>We're populating your statistics cache for the first time.</p>
          <p>This may take a moment while we gather your project and task data...</p>
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  // Handle error state (but show data if available from cache)
  if (error && !statistics) {
    return (
      <div className="home-page">
        <div className="cache-error">
          <div className="error-icon">⚠️</div>
          <h2>Unable to Load Dashboard</h2>
          <p>{error}</p>
          {error.includes('Settings') ? (
            <Link to="/settings" className="btn-primary">
              Go to Settings
            </Link>
          ) : (
            <button 
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="home-error">
        <p>No data available</p>
      </div>
    );
  }

  const user = statistics.user || {};
  const stats = statistics.statistics || {};
  const cacheStatus = getCacheStatusDisplay();

  return (
    <div className="home-container">
      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="welcome-header">
          <div>
            <h1>Welcome back, {user.fullName || 'User'}!</h1>
            <p className="user-email">{user.emailId}</p>
          </div>
          
          {/* Cache Status Indicator */}
          <div className="cache-status-container">
            {cacheStatus && (
              <div className={`cache-status ${cacheStatus.class}`}>
                <span className={`status-icon ${statistics.cache_status === 'updating' ? 'rotating' : ''}`}>
                  {cacheStatus.icon}
                </span>
                <span className="status-text">{cacheStatus.text}</span>
                {statistics.last_updated && (
                  <span className="last-updated">
                    • Updated {formatLastUpdated(statistics.last_updated)}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card primary">
          <div className="stat-icon">📁</div>
          <div className="stat-content">
            <div className="stat-value">{stats.projects_count || 0}</div>
            <div className="stat-label">Assigned Projects</div>
          </div>
        </div>

        <div className="stat-card info">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{stats.active_tasks || 0}</div>
            <div className="stat-label">Active Tasks</div>
          </div>
        </div>

        <div className="stat-card success">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.completed_tasks || 0}</div>
            <div className="stat-label">Completed Tasks</div>
          </div>
        </div>

        <div className={`stat-card ${(stats.overdue_tasks || 0) > 0 ? 'danger' : 'secondary'}`}>
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <div className="stat-value">{stats.overdue_tasks || 0}</div>
            <div className="stat-label">Overdue Tasks</div>
          </div>
        </div>

        <div className={`stat-card ${(stats.at_risk_tasks || 0) > 0 ? 'warning' : 'secondary'}`}>
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.at_risk_tasks || 0}</div>
            <div className="stat-label">Tasks at Risk</div>
          </div>
        </div>

        <div className="stat-card accent">
          <div className="stat-icon">📅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.due_this_week || 0}</div>
            <div className="stat-label">Due This Week</div>
          </div>
        </div>

        <div className="stat-card secondary">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">{(stats.hours_logged_this_week || 0).toFixed(1)}h</div>
            <div className="stat-label">Logged This Week</div>
          </div>
        </div>

        <div className="stat-card secondary">
          <div className="stat-icon">📝</div>
          <div className="stat-content">
            <div className="stat-value">{Math.ceil((stats.hours_logged_this_week || 0) / 2)}</div>
            <div className="stat-label">Time Entries This Week</div>
          </div>
        </div>
      </div>

      {/* Main Content Grid - Sections temporarily disabled pending API enhancement */}
      {/* TODO: Implement these sections when API provides the necessary data:
          - Recent Projects
          - Upcoming Milestones  
          - Task Status Distribution
          - Priority Distribution
      */}

      {/* Quick Actions */}
      <div className="quick-actions">
        <Link to="/projects" className="action-button">
          View All Projects →
        </Link>
      </div>
    </div>
  );
};

export default Home;