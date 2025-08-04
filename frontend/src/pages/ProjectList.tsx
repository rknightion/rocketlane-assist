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
      } else {
        setError('Failed to load projects. Please check your configuration.');
      }
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading projects...</div>;
  if (error) return <div className="error">{error}</div>;

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
