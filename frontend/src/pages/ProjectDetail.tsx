import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { projectsApi, Project, Task, TaskSummary } from '../services/api';
import { trackEvent, measurePerformance } from '../lib/observability';

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [summary, setSummary] = useState<TaskSummary | null>(null);
  const [streamingSummary, setStreamingSummary] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjectData = useCallback(async () => {
    const startTime = Date.now();
    try {
      setLoading(true);
      const [projectData, tasksData] = await Promise.all([
        projectsApi.getProject(projectId!),
        projectsApi.getProjectTasks(projectId!, 'not_done')
      ]);
      setProject(projectData);
      setTasks(tasksData);

      // Track successful project load
      trackEvent('project_loaded', {
        projectId: projectId!,
        taskCount: tasksData.length,
        projectName: projectData.projectName
      });

      // Measure performance
      measurePerformance('project_load_time', Date.now() - startTime, {
        projectId: projectId!
      });
    } catch (err) {
      // Check if it's a user ID configuration error
      const error = err as { response?: { status?: number; data?: { detail?: string } } };
      if (error.response?.status === 403 && error.response?.data?.detail?.includes('User ID not configured')) {
        setError('Please select your user account in Settings to view project details.');
      } else {
        setError('Failed to load project details.');
      }

      // Track error
      trackEvent('project_load_error', {
        projectId: projectId!,
        error: error instanceof Error ? error.message : 'Unknown error',
        statusCode: (error as { response?: { status?: number } }).response?.status
      });
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadProjectData();
    }
  }, [projectId, loadProjectData]);

  const handleSummarize = async () => {
    const startTime = Date.now();
    try {
      setSummarizing(true);
      setSummary(null);
      setStreamingSummary('');

      // Track summarization attempt
      trackEvent('summarization_started', {
        projectId: projectId!,
        projectName: project?.projectName,
        taskCount: tasks.length,
        streaming: true
      });

      // Always use streaming API
      let fullSummary = '';
      let metadata: any = null;
      
      for await (const event of projectsApi.summarizeProjectTasksStream(projectId!)) {
        if (event.type === 'metadata') {
          metadata = event.data;
        } else if (event.type === 'chunk') {
          fullSummary += event.data;
          setStreamingSummary(fullSummary);
        } else if (event.type === 'done') {
          // Create the final summary object
          setSummary({
            project_id: projectId!,
            project_name: metadata?.project_name || project?.projectName || '',
            summary: fullSummary,
            task_count: metadata?.task_count || tasks.length,
            tasks: tasks
          });
          setStreamingSummary('');
        }
      }

      // Track successful summarization
      trackEvent('summarization_completed', {
        projectId: projectId!,
        projectName: project?.projectName,
        summaryLength: summary?.summary.length || streamingSummary.length,
        streaming: true
      });

      // Measure performance
      measurePerformance('summarization_time', Date.now() - startTime, {
        projectId: projectId!,
        taskCount: tasks.length,
        streaming: true
      });
    } catch (err) {
      // Check if it's a user ID configuration error
      const error = err as { response?: { status?: number; data?: { detail?: string } } };
      if (error.response?.status === 403 && error.response?.data?.detail?.includes('User ID not configured')) {
        setError('Please select your user account in Settings to generate summaries.');
      } else {
        setError('Failed to generate summary.');
      }

      // Track error
      trackEvent('summarization_error', {
        projectId: projectId!,
        error: error instanceof Error ? error.message : 'Unknown error',
        statusCode: (error as { response?: { status?: number } }).response?.status,
        streaming: true
      });
    } finally {
      setSummarizing(false);
    }
  };

  if (loading) return <div className="loading">Loading project details...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!project) return <div className="error">Project not found</div>;

  return (
    <div className="project-detail">
      <button onClick={() => navigate('/')} className="back-button">
        ← Back to Projects
      </button>

      <h2>{project.projectName}</h2>
      {project.description && <p className="project-description">{project.description}</p>}

      <div className="tasks-section">
        <h3>Outstanding Tasks ({tasks.length})</h3>

        <button
          onClick={handleSummarize}
          disabled={summarizing || tasks.length === 0}
          className="summarize-button"
        >
          {summarizing ? 'Generating Summary...' : 'Summarize Tasks'}
        </button>

        {(summary || streamingSummary) && (
          <div className="summary-section">
            <h4>AI Summary</h4>
            <div className="summary-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {summary?.summary || streamingSummary}
              </ReactMarkdown>
              {summarizing && (
                <span className="streaming-indicator">▊</span>
              )}
            </div>
          </div>
        )}

        <div className="tasks-list">
          {tasks.length === 0 ? (
            <p>No outstanding tasks.</p>
          ) : (
            tasks.map((task) => (
              <div key={task.taskId} className="task-item">
                <h4>{task.taskName}</h4>
                {task.description && <p>{task.description}</p>}
                <div className="task-meta">
                  {task.dueDate && <span>Due: {task.dueDate}</span>}
                  {task.assignees?.members && task.assignees.members.length > 0 && (
                    <span>
                      Assigned to: {task.assignees.members.map(m =>
                        `${m.firstName || ''} ${m.lastName || ''}`.trim() || m.emailId
                      ).join(', ')}
                    </span>
                  )}
                  {task.priority && <span>Priority: {task.priority.label}</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default ProjectDetail;
