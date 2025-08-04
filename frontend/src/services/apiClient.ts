import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

// API Error type
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, any>;
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId();

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Try to refresh token
      try {
        await refreshAuthToken();
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle network errors
    if (!error.response) {
      throw {
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      } as ApiError;
    }

    // Handle API errors
    const apiError: ApiError = {
      message: error.response.data?.message || 'An unexpected error occurred',
      code: error.response.data?.code,
      status: error.response.status,
      details: error.response.data?.details,
    };

    throw apiError;
  }
);

// Utility functions
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

async function refreshAuthToken(): Promise<void> {
  // Implement token refresh logic
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) throw new Error('No refresh token');

  const response = await axios.post('/api/v1/auth/refresh', { refreshToken });
  localStorage.setItem('authToken', response.data.accessToken);
  localStorage.setItem('refreshToken', response.data.refreshToken);
}

// Retry configuration
const retryConfig = {
  retries: 3,
  retryDelay: (retryCount: number) => {
    return Math.min(1000 * Math.pow(2, retryCount), 10000);
  },
  retryCondition: (error: AxiosError) => {
    return !error.response || error.response.status >= 500;
  },
};

// Generic request wrapper with retry logic
export async function apiRequest<T>(
  config: AxiosRequestConfig,
  options?: { skipRetry?: boolean }
): Promise<T> {
  let lastError: any;
  const maxRetries = options?.skipRetry ? 0 : retryConfig.retries;

  for (let i = 0; i <= maxRetries; i++) {
    try {
      const response = await apiClient(config);
      return response.data;
    } catch (error) {
      lastError = error;

      if (i < maxRetries && retryConfig.retryCondition(error as AxiosError)) {
        await new Promise(resolve =>
          setTimeout(resolve, retryConfig.retryDelay(i))
        );
      } else {
        break;
      }
    }
  }

  throw lastError;
}

// Convenience methods
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'GET', url }),

  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'POST', url, data }),

  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PUT', url, data }),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'DELETE', url }),

  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PATCH', url, data }),
};

export default apiClient;
