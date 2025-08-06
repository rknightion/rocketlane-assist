import axios from 'axios';
import { faro } from '@grafana/faro-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptor to propagate trace context
api.interceptors.request.use((config) => {
  // Get current trace context from Faro if available
  const faroInstance = faro;
  if (faroInstance && faroInstance.api?.getOTEL) {
    const otel = faroInstance.api.getOTEL();
    if (otel) {
      const activeSpan = otel.trace.getActiveSpan();
      if (activeSpan) {
        const spanContext = activeSpan.spanContext();
        if (spanContext) {
          // Add W3C Trace Context headers
          config.headers['traceparent'] = `00-${spanContext.traceId}-${spanContext.spanId}-01`;
          // Add baggage for service namespace correlation
          config.headers['baggage'] = 'service.namespace=rocketlane';
        }
      }
    }
  }
  return config;
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
  rocketlane_user_id?: string;
}

export interface User {
  userId: string;
  emailId: string;
  firstName: string;
  lastName: string;
  fullName: string;
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

  summarizeProjectTasksStream: async function* (projectId: string): AsyncGenerator<{ type: string; data?: any }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/summarize/stream`, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data) {
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    }
  },
};

export const configApi = {
  getConfig: async (): Promise<Config> => {
    const response = await api.get<Config>('/config/');
    return response.data;
  },

  updateConfig: async (config: {
    llm_provider?: 'openai' | 'anthropic';
    llm_model?: string;
    openai_api_key?: string;
    anthropic_api_key?: string;
    rocketlane_api_key?: string;
    rocketlane_user_id?: string;
  }): Promise<Config> => {
    const response = await api.put('/config/', config);
    return response.data;
  },
};

export const usersApi = {
  getUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/users/');
    return response.data;
  },
};

export const statisticsApi = {
  getUserStatistics: async (): Promise<any> => {
    const response = await api.get('/statistics/');
    return response.data;
  },
};

export const timesheetsApi = {
  getCategories: async (): Promise<any[]> => {
    const response = await api.get('/timesheets/categories');
    return response.data;
  },
  
  getTasks: async (projectId?: string): Promise<any[]> => {
    const params = projectId ? { project_id: projectId } : {};
    const response = await api.get('/timesheets/tasks', { params });
    return response.data;
  },
  
  getProjects: async (): Promise<any[]> => {
    const response = await api.get('/timesheets/projects');
    return response.data;
  },
  
  getEntries: async (dateFrom?: string, dateTo?: string, projectId?: string): Promise<any[]> => {
    const params: any = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (projectId) params.project_id = projectId;
    
    const response = await api.get('/timesheets/entries', { params });
    return response.data;
  },
  
  createEntry: async (entry: {
    date: string;
    minutes: number;
    task_id?: string;
    project_id?: string;
    activity_name?: string;
    notes?: string;
    billable?: boolean;
    category_id?: string;
  }): Promise<any> => {
    const response = await api.post('/timesheets/entries', entry);
    return response.data;
  },
  
  updateEntry: async (entryId: string, entry: any): Promise<any> => {
    const response = await api.put(`/timesheets/entries/${entryId}`, entry);
    return response.data;
  },
  
  deleteEntry: async (entryId: string): Promise<void> => {
    await api.delete(`/timesheets/entries/${entryId}`);
  },
  
  getSummary: async (dateFrom?: string, dateTo?: string): Promise<any> => {
    const params: any = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    
    const response = await api.get('/timesheets/summary', { params });
    return response.data;
  },
};
