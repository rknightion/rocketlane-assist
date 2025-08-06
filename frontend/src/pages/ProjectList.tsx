import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi, Project } from '../services/api';

function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (err: any) {
      // Check if it's a user ID configuration error
      if (err.response?.status === 403 && err.response?.data?.detail?.includes('User ID not configured')) {
        setError('Please select your user account in Settings to view projects.');
      } else if (err.response?.status === 503 || (err.response?.status === 500 && err.response?.data?.detail?.includes('cache'))) {
        // Service temporarily unavailable or cache building
        setError('Building project cache, please wait a moment and refresh...');
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Failed to load projects. Please check your configuration in Settings.');
      } else {
        setError('Unable to load projects. The system may be initializing, please try again in a moment.');
      }
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading projects...</div>;
  if (error) return (
    <div className="error">
      <p>{error}</p>
      {error.includes('cache') && (
        <button 
          onClick={loadProjects} 
          className="summarize-button"
          style={{ marginTop: '1rem' }}
        >
          Retry
        </button>
      )}
    </div>
  );

  return (
    <div className="project-list">
      <h2>Projects</h2>
      {projects.length === 0 ? (
        <p>No projects found.</p>
      ) : (
        <div className="project-grid">
          {projects.map((project) => (
            <Link
              key={project.projectId}
              to={`/projects/${project.projectId}`}
              className="project-card"
            >
              <h3>{project.projectName}</h3>
              {project.description && <p>{project.description}</p>}
              {project.status && (
                <span className={`status status-${project.status.label.toLowerCase().replace(' ', '-')}`}>
                  {project.status.label}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProjectList;
