import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Project {
  projectId: string;
  projectName: string;
  description?: string;
  status?: {
    value: number;
    label: string;
  };
}

export interface Task {
  taskId: string;
  taskName: string;
  description?: string;
  status: {
    value: number;
    label: string;
  };
  dueDate?: string;
  assignees?: {
    members?: Array<{
      emailId: string;
      userId: number;
      firstName?: string;
      lastName?: string;
    }>;
  };
  priority?: {
    value: number;
    label: string;
  };
}

export interface TaskSummary {
  project_id: string;
  project_name: string;
  summary: string;
  task_count: number;
  tasks: Task[];
}

export interface Config {
  llm_provider: 'openai' | 'anthropic';
  llm_model: string;
  has_openai_key: boolean;
  has_anthropic_key: boolean;
  has_rocketlane_key: boolean;
}

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get<Project[]>('/projects/');
    return response.data;
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  getProjectTasks: async (projectId: string, status?: string): Promise<Task[]> => {
    const params = status ? { status } : {};
    const response = await api.get<Task[]>(`/projects/${projectId}/tasks`, { params });
    return response.data;
  },

  summarizeProjectTasks: async (projectId: string): Promise<TaskSummary> => {
    const response = await api.post<TaskSummary>(`/projects/${projectId}/summarize`);
    return response.data;
  },
};

export const configApi = {
  getConfig: async (): Promise<Config> => {
    const response = await api.get<Config>('/config/');
    return response.data;
  },

  updateConfig: async (config: Partial<Config>): Promise<any> => {
    const response = await api.put('/config/', config);
    return response.data;
  },
};