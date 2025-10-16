// Auth-related TypeScript interfaces for authentication flows

export interface LoginRequest {
  email: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface ErrorResponse {
  detail: {
    error: {
      code: string
      message: string
      timestamp: string
      request_id: string
    }
  }
}

export interface AuthContextType {
  isAuthenticated: boolean
  userToken: string | null
  login: (token: string) => void
  logout: () => void
}
