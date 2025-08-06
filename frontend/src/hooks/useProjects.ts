import { useState, useEffect, useCallback, useMemo } from 'react';
import { debounce } from '../utils/debounce';
import { api, ApiError } from '../services/apiClient';

// Types
export interface Project {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'on-hold' | 'cancelled';
  client: {
    id: string;
    name: string;
  };
  startDate: string;
  endDate: string;
  progress: number;
  healthScore: number;
  tasks: Task[];
}

export interface Task {
  id: string;
  name: string;
  status: 'pending' | 'in-progress' | 'completed';
  assignee: string;
  dueDate: string;
  priority: 'low' | 'medium' | 'high';
}

export interface ProjectFilters {
  status?: Project['status'];
  clientId?: string;
  search?: string;
  sortBy?: 'name' | 'startDate' | 'progress' | 'healthScore';
  sortOrder?: 'asc' | 'desc';
}

interface UseProjectsState {
  projects: Project[];
  isLoading: boolean;
  error: ApiError | null;
  hasMore: boolean;
  page: number;
}

interface UseProjectsReturn extends UseProjectsState {
  fetchProjects: () => Promise<void>;
  fetchMore: () => Promise<void>;
  refetch: () => Promise<void>;
  updateFilters: (filters: Partial<ProjectFilters>) => void;
  clearError: () => void;
}

const PROJECTS_PER_PAGE = 20;

export function useProjects(initialFilters?: ProjectFilters): UseProjectsReturn {
  const [state, setState] = useState<UseProjectsState>({
    projects: [],
    isLoading: false,
    error: null,
    hasMore: true,
    page: 1,
  });

  const [filters, setFilters] = useState<ProjectFilters>(initialFilters || {});

  // Debounced search
  const debouncedSearch = useMemo(
    () => debounce((search: string) => {
      setFilters(prev => ({ ...prev, search }));
      setState(prev => ({ ...prev, page: 1, projects: [] }));
    }, 300),
    []
  );

  // Fetch projects
  const fetchProjects = useCallback(async (page: number = 1, append: boolean = false) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: PROJECTS_PER_PAGE.toString(),
        ...(filters.status && { status: filters.status }),
        ...(filters.clientId && { clientId: filters.clientId }),
        ...(filters.search && { search: filters.search }),
        ...(filters.sortBy && { sortBy: filters.sortBy }),
        ...(filters.sortOrder && { sortOrder: filters.sortOrder }),
      });

      const response = await api.get<{
        projects: Project[];
        total: number;
        page: number;
        limit: number;
      }>(`/projects?${params.toString()}`);

      setState(prev => ({
        ...prev,
        projects: append ? [...prev.projects, ...response.projects] : response.projects,
        isLoading: false,
        hasMore: response.projects.length === PROJECTS_PER_PAGE,
        page,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as ApiError,
      }));
    }
  }, [filters]);

  // Fetch more projects (pagination)
  const fetchMore = useCallback(async () => {
    if (!state.hasMore || state.isLoading) return;

    const nextPage = state.page + 1;
    await fetchProjects(nextPage, true);
  }, [state.page, state.hasMore, state.isLoading, fetchProjects]);

  // Refetch projects
  const refetch = useCallback(async () => {
    setState(prev => ({ ...prev, page: 1, projects: [] }));
    await fetchProjects(1, false);
  }, [fetchProjects]);

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<ProjectFilters>) => {
    if (newFilters.search !== undefined) {
      debouncedSearch(newFilters.search);
    } else {
      setFilters(prev => ({ ...prev, ...newFilters }));
      setState(prev => ({ ...prev, page: 1, projects: [] }));
    }
  }, [debouncedSearch]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchProjects();
  }, [filters, fetchProjects]);

  // Cleanup
  useEffect(() => {
    return () => {
      debouncedSearch.cancel();
    };
  }, [debouncedSearch]);

  return {
    ...state,
    fetchProjects: () => fetchProjects(1, false),
    fetchMore,
    refetch,
    updateFilters,
    clearError,
  };
}

// Hook for single project
export function useProject(projectId: string) {
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchProject = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.get<Project>(`/projects/${projectId}`);
      setProject(data);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  return {
    project,
    isLoading,
    error,
    refetch: fetchProject,
  };
}
