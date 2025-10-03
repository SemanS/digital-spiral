import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { handleApiError } from './errors';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token if available
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('auth_token');
          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Retry logic with exponential backoff
        if (
          error.response?.status &&
          error.response.status >= 500 &&
          originalRequest &&
          !originalRequest._retry
        ) {
          originalRequest._retry = true;

          const retryCount = (originalRequest as any).__retryCount || 0;
          if (retryCount < 3) {
            (originalRequest as any).__retryCount = retryCount + 1;
            const delay = Math.min(1000 * 2 ** retryCount, 30000);
            await new Promise((resolve) => setTimeout(resolve, delay));
            return this.client(originalRequest);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  getInstance(): AxiosInstance {
    return this.client;
  }

  async get<T>(url: string, config?: any): Promise<T> {
    try {
      const response = await this.client.get<T>(url, config);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response = await this.client.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  }

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response = await this.client.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    try {
      const response = await this.client.delete<T>(url, config);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  }
}

export const apiClient = new ApiClient();
export default apiClient;

