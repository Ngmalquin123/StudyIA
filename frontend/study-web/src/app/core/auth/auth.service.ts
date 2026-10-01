import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import {
  Observable,
  catchError,
  finalize,
  map,
  of,
  shareReplay,
  switchMap,
  tap,
  throwError,
} from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginRequest, LoginResponse, RegisterRequest, Tokens, User } from './auth.models';
import { TokenStorage } from './token-storage';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly storage = inject(TokenStorage);
  private readonly api = `${environment.apiUrl}/auth`;

  private readonly currentUser = signal<User | null>(null);
  // Si varias peticiones reciben 401 a la vez, todas esperan el mismo refresh
  private refreshInFlight$: Observable<Tokens> | null = null;

  readonly user = this.currentUser.asReadonly();
  readonly isLoggedIn = computed(() => this.currentUser() !== null);
  readonly isAdmin = computed(() => this.currentUser()?.rol === 'admin');

  login(data: LoginRequest): Observable<User> {
    return this.http.post<LoginResponse>(`${this.api}/login`, data).pipe(
      tap((response) => {
        this.storage.save(response);
        this.currentUser.set(response.user);
      }),
      map((response) => response.user),
    );
  }

  /** Crea la cuenta e inicia sesión con ella. */
  register(data: RegisterRequest): Observable<User> {
    return this.http
      .post<User>(`${this.api}/register`, data)
      .pipe(switchMap(() => this.login({ email: data.email, password: data.password })));
  }

  refresh(): Observable<Tokens> {
    const refreshToken = this.storage.refreshToken;
    if (!refreshToken) {
      return throwError(() => new Error('No hay refresh token'));
    }
    if (!this.refreshInFlight$) {
      this.refreshInFlight$ = this.http
        .post<Tokens>(`${this.api}/refresh`, { refresh_token: refreshToken })
        .pipe(
          tap((tokens) => this.storage.save(tokens)),
          finalize(() => (this.refreshInFlight$ = null)),
          shareReplay(1),
        );
    }
    return this.refreshInFlight$;
  }

  /** Al abrir la app: si hay tokens guardados, recupera el usuario con /me. */
  restoreSession(): Observable<User | null> {
    if (!this.storage.accessToken && !this.storage.refreshToken) {
      return of(null);
    }
    return this.http.get<User>(`${this.api}/me`).pipe(
      tap((user) => this.currentUser.set(user)),
      catchError(() => {
        this.clearSession();
        return of(null);
      }),
    );
  }

  /** Actualiza el usuario en memoria (por ejemplo, después de editar el perfil). */
  setUser(user: User): void {
    this.currentUser.set(user);
  }

  logout(): void {
    this.clearSession();
    void this.router.navigateByUrl('/login');
  }

  clearSession(): void {
    this.storage.clear();
    this.currentUser.set(null);
  }
}
