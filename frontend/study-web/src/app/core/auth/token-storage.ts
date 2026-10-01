import { Injectable } from '@angular/core';
import { Tokens } from './auth.models';

const ACCESS_KEY = 'studyia.access_token';
const REFRESH_KEY = 'studyia.refresh_token';

/**
 * Guarda los tokens en localStorage para que la sesión sobreviva a recargar la página.
 * Si el navegador bloquea el almacenamiento (modo privado), la sesión dura lo que dure la pestaña.
 */
@Injectable({ providedIn: 'root' })
export class TokenStorage {
  private memory: Partial<Record<string, string>> = {};

  get accessToken(): string | null {
    return this.read(ACCESS_KEY);
  }

  get refreshToken(): string | null {
    return this.read(REFRESH_KEY);
  }

  save(tokens: Tokens): void {
    this.write(ACCESS_KEY, tokens.access_token);
    this.write(REFRESH_KEY, tokens.refresh_token);
  }

  clear(): void {
    this.memory = {};
    try {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      // almacenamiento no disponible: ya se limpió la memoria
    }
  }

  private read(key: string): string | null {
    try {
      return localStorage.getItem(key) ?? this.memory[key] ?? null;
    } catch {
      return this.memory[key] ?? null;
    }
  }

  private write(key: string, value: string): void {
    this.memory[key] = value;
    try {
      localStorage.setItem(key, value);
    } catch {
      // se queda solo en memoria
    }
  }
}
