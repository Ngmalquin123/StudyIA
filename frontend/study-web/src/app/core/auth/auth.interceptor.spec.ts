import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';
import { API, fakeTokens, fakeUser } from './auth.testing';
import { TokenStorage } from './token-storage';

describe('authInterceptor', () => {
  let client: HttpClient;
  let http: HttpTestingController;
  let storage: TokenStorage;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    client = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
    storage = TestBed.inject(TokenStorage);
    storage.save(fakeTokens);
  });

  afterEach(() => http.verify());

  it('agrega el Bearer solo a las peticiones del backend', () => {
    client.get(`${API}/users`).subscribe();
    client.get('https://otro-sitio.com/datos').subscribe();
    expect(http.expectOne(`${API}/users`).request.headers.get('Authorization')).toBe('Bearer access-1');
    expect(http.expectOne('https://otro-sitio.com/datos').request.headers.has('Authorization')).toBe(false);
  });

  it('con 401 refresca el token y repite la petición', () => {
    let body: unknown;
    client.get(`${API}/auth/me`).subscribe((response) => (body = response));

    http.expectOne(`${API}/auth/me`).flush({ detail: 'expirado' }, { status: 401, statusText: 'Unauthorized' });

    const refresh = http.expectOne(`${API}/auth/refresh`);
    expect(refresh.request.body).toEqual({ refresh_token: 'refresh-1' });
    refresh.flush({ ...fakeTokens, access_token: 'access-2', refresh_token: 'refresh-2' });

    const retry = http.expectOne(`${API}/auth/me`);
    expect(retry.request.headers.get('Authorization')).toBe('Bearer access-2');
    retry.flush(fakeUser);

    expect(body).toEqual(fakeUser);
    expect(storage.refreshToken).toBe('refresh-2');
  });

  it('dos 401 simultáneos comparten un solo refresh', () => {
    client.get(`${API}/auth/me`).subscribe();
    client.get(`${API}/roles`).subscribe();
    for (const url of [`${API}/auth/me`, `${API}/roles`]) {
      http.expectOne(url).flush({}, { status: 401, statusText: 'Unauthorized' });
    }
    http.expectOne(`${API}/auth/refresh`).flush({ ...fakeTokens, access_token: 'access-2' });
    http.expectOne(`${API}/auth/me`).flush(fakeUser);
    http.expectOne(`${API}/roles`).flush([]);
  });

  it('si el refresh falla cierra la sesión y va al login', () => {
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    TestBed.inject(AuthService).setUser(fakeUser);
    let failed = false;
    client.get(`${API}/auth/me`).subscribe({ error: () => (failed = true) });

    http.expectOne(`${API}/auth/me`).flush({}, { status: 401, statusText: 'Unauthorized' });
    http.expectOne(`${API}/auth/refresh`).flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(failed).toBe(true);
    expect(storage.accessToken).toBeNull();
    expect(TestBed.inject(AuthService).isLoggedIn()).toBe(false);
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  it('un 401 del login no intenta refrescar', () => {
    client.post(`${API}/auth/login`, {}).subscribe({ error: () => undefined });
    http.expectOne(`${API}/auth/login`).flush({}, { status: 401, statusText: 'Unauthorized' });
    http.expectNone(`${API}/auth/refresh`);
  });
});
