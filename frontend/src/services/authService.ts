/**
 * Authentication service for managing user login, registration, and JWT tokens.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  gmail_connected: boolean;
  created_at: string;
  last_login?: string;
  last_sync?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'email2kg_token';
  private readonly USER_KEY = 'email2kg_user';

  /**
   * Helper to safely parse error responses
   */
  private async parseErrorResponse(response: Response): Promise<string> {
    const contentType = response.headers.get('content-type');

    // Check if response is JSON
    if (contentType && contentType.includes('application/json')) {
      try {
        const error = await response.json();
        return error.detail || error.message || 'Request failed';
      } catch (e) {
        return `Request failed with status ${response.status}`;
      }
    }

    // If not JSON, try to get text (might be HTML error page)
    try {
      const text = await response.text();
      // If it's HTML, return a generic message
      if (text.startsWith('<')) {
        return `Server error (${response.status}): Unable to connect to API. Please check if the backend is running.`;
      }
      return text || `Request failed with status ${response.status}`;
    } catch (e) {
      return `Request failed with status ${response.status}`;
    }
  }

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorMessage = await this.parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Login user and store JWT token
   */
  async login(credentials: LoginCredentials): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorMessage = await this.parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    const tokenData: AuthToken = await response.json();
    this.setToken(tokenData.access_token);

    // Fetch user data
    const user = await this.getCurrentUser();
    this.setUser(user);

    return user;
  }

  /**
   * Logout user and clear stored data
   */
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
      }
      throw new Error('Failed to get user information');
    }

    const user = await response.json();
    this.setUser(user);
    return user;
  }

  /**
   * Update user profile
   */
  async updateProfile(data: { full_name?: string; email?: string }): Promise<User> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorMessage = await this.parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    const user = await response.json();
    this.setUser(user);
    return user;
  }

  /**
   * Change user password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorMessage = await this.parseErrorResponse(response);
      throw new Error(errorMessage);
    }
  }

  /**
   * Get stored JWT token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Store JWT token
   */
  private setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get stored user data
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Store user data
   */
  private setUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Get authorization header for API requests
   */
  getAuthHeader(): { Authorization: string } | {} {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export const authService = new AuthService();
