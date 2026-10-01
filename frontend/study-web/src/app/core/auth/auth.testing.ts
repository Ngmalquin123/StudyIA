import { User } from './auth.models';

export const API = 'http://localhost:8000/api';

export const fakeUser: User = {
  id: 1,
  name: 'Ana',
  email: 'ana@studyia.com',
  rol: 'estudiante',
  is_active: true,
  created_at: '2026-09-30T00:00:00Z',
};

export const fakeTokens = { access_token: 'access-1', refresh_token: 'refresh-1', token_type: 'bearer' };
