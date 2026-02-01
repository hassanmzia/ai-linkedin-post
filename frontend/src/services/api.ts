import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://172.168.1.95:4052';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor - attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/auth/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login/', { username, password }),
  register: (data: { username: string; email: string; password: string; password_confirm: string }) =>
    api.post('/auth/register/', data),
  me: () => api.get('/auth/me/'),
};

// Config
export const configAPI = {
  get: () => api.get('/config/'),
  update: (data: Record<string, string>) => api.patch('/config/', data),
};

// Templates
export const templatesAPI = {
  list: () => api.get('/templates/'),
  get: (id: string) => api.get(`/templates/${id}/`),
  create: (data: Record<string, unknown>) => api.post('/templates/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/templates/${id}/`, data),
  delete: (id: string) => api.delete(`/templates/${id}/`),
};

// Projects
export const projectsAPI = {
  list: (params?: Record<string, string>) => api.get('/projects/', { params }),
  get: (id: string) => api.get(`/projects/${id}/`),
  create: (data: Record<string, unknown>) => api.post('/projects/', data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/projects/${id}/`, data),
  delete: (id: string) => api.delete(`/projects/${id}/`),
  generate: (id: string) => api.post(`/projects/${id}/generate/`),
  regenerate: (id: string, feedback?: string) =>
    api.post(`/projects/${id}/regenerate/`, { feedback }),
  evaluate: (id: string) => api.post(`/projects/${id}/evaluate/`),
  toggleFavorite: (id: string) => api.post(`/projects/${id}/toggle_favorite/`),
  publish: (id: string) => api.post(`/projects/${id}/publish/`),
  updatePost: (id: string, content: string) =>
    api.post(`/projects/${id}/update_post/`, { content }),
};

// Runs
export const runsAPI = {
  list: () => api.get('/runs/'),
  get: (id: string) => api.get(`/runs/${id}/`),
};

// Analytics
export const analyticsAPI = {
  list: (projectId?: string) =>
    api.get('/analytics/', { params: projectId ? { project: projectId } : {} }),
  create: (data: Record<string, unknown>) => api.post('/analytics/', data),
};

// Hashtags
export const hashtagsAPI = {
  list: () => api.get('/hashtags/'),
  create: (data: { tag: string; category?: string }) => api.post('/hashtags/', data),
  delete: (id: number) => api.delete(`/hashtags/${id}/`),
};

// Calendar
export const calendarAPI = {
  list: (params?: Record<string, string>) => api.get('/calendar/', { params }),
  create: (data: Record<string, unknown>) => api.post('/calendar/', data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/calendar/${id}/`, data),
  delete: (id: string) => api.delete(`/calendar/${id}/`),
};

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard/'),
};
