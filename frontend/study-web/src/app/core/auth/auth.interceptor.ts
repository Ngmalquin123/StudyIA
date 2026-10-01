import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { TokenStorage } from './token-storage';

// Rutas que no llevan token ni deben intentar un refresh al recibir 401
const PUBLIC_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh'];

function withToken(request: HttpRequest<unknown>, token: string | null): HttpRequest<unknown> {
  return token ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : request;
}

/**
 * Agrega el access token a las peticiones al backend. Si el backend responde 401
 * (token expirado), pide tokens nuevos con el refresh token y repite la petición una vez.
 * Si el refresh también falla, cierra la sesión y manda al login.
 */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const isApi = request.url.startsWith(environment.apiUrl);
  const isPublic = PUBLIC_ENDPOINTS.some((path) => request.url.endsWith(path));
  if (!isApi || isPublic) {
    return next(request);
  }

  const auth = inject(AuthService);
  const storage = inject(TokenStorage);

  return next(withToken(request, storage.accessToken)).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401 || !storage.refreshToken) {
        return throwError(() => error);
      }
      return auth.refresh().pipe(
        catchError((refreshError: unknown) => {
          auth.logout();
          return throwError(() => refreshError);
        }),
        switchMap((tokens) => next(withToken(request, tokens.access_token))),
      );
    }),
  );
};
