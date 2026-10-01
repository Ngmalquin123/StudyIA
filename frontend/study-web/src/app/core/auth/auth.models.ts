// Mismos campos que los schemas de backend/src/studyia/schemas/

export interface User {
  id: number;
  name: string;
  email: string;
  rol: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse extends Tokens {
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}
