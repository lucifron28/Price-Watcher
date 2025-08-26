const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface LoginResponse {
  access: string;
  user: User;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginData {
  username: string;
  password: string;
}

class ApiError extends Error {
  public status?: number;
  
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.loadTokenFromStorage();
  }

  private loadTokenFromStorage() {
    this.accessToken = localStorage.getItem('access_token');
  }

  setAccessToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('access_token', token);
  }

  clearAccessToken() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.accessToken) {
      headers.Authorization = `Bearer ${this.accessToken}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Include cookies for refresh token
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      return response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError('Network error or server unavailable');
    }
  }

  // Auth endpoints
  async register(data: RegisterData): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    this.setAccessToken(response.access);
    return response;
  }

  async login(data: LoginData): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    this.setAccessToken(response.access);
    return response;
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout/', {
      method: 'POST',
    });
    
    this.clearAccessToken();
  }

  async refreshToken(): Promise<{ access: string }> {
    const response = await this.request<{ access: string }>('/auth/refresh/', {
      method: 'POST',
    });
    
    this.setAccessToken(response.access);
    return response;
  }

  async getUserProfile(): Promise<User> {
    return this.request<User>('/auth/profile/');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.accessToken !== null;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
export { ApiError };
