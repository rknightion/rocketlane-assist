# API & HTTP Layer

## API Client Structure
```typescript
// services/api.ts
class ApiClient {
  private baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
}
```

## Service Functions
```typescript
// Specific API operations
export const projectApi = {
  getProjects: () => apiClient.request<Project[]>('/api/v1/projects/'),
  getProject: (id: string) => apiClient.request<Project>(`/api/v1/projects/${id}`),
  getTasks: (projectId: string) => apiClient.request<Task[]>(`/api/v1/projects/${projectId}/tasks`),
  summarizeProject: (projectId: string) => apiClient.request<Summary>(`/api/v1/projects/${projectId}/summarize`)
};
```

## Service Rules
- **Single API client** - reuse across all services
- **Error handling** - convert HTTP errors to user messages  
- **Type safety** - typed responses for all endpoints
- **Base URL** - configurable via environment variables
- **Request headers** - consistent Content-Type and auth