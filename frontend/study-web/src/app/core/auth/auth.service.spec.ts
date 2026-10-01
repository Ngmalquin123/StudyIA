import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';
import { API, fakeTokens, fakeUser } from './auth.testing';
import { TokenStorage } from './token-storage';

describe('AuthService', () => {
  let auth: AuthService;
  let storage: TokenStorage;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    auth = TestBed.inject(AuthService);
    storage = TestBed.inject(TokenStorage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('login guarda los tokens y el usuario', () => {
    auth.login({ email: 'ana@studyia.com', password: 'Clave12345' }).subscribe();
    const request = http.expectOne(`${API}/auth/login`);
    expect(request.request.headers.has('Authorization')).toBe(false);
    request.flush({ ...fakeTokens, user: fakeUser });

    expect(storage.accessToken).toBe('access-1');
    expect(storage.refreshToken).toBe('refresh-1');
    expect(auth.isLoggedIn()).toBe(true);
    expect(auth.isAdmin()).toBe(false);
  });

  it('register crea la cuenta y luego inicia sesión', () => {
    auth.register({ name: 'Ana', email: 'ana@studyia.com', password: 'Clave12345' }).subscribe();
    http.expectOne(`${API}/auth/register`).flush(fakeUser);
    http.expectOne(`${API}/auth/login`).flush({ ...fakeTokens, user: fakeUser });
    expect(auth.user()?.email).toBe('ana@studyia.com');
  });

  it('restoreSession sin tokens no llama al backend', () => {
    let result: unknown = 'sin-respuesta';
    auth.restoreSession().subscribe((user) => (result = user));
    expect(result).toBeNull();
  });

  it('restoreSession con token recupera el usuario', () => {
    storage.save(fakeTokens);
    auth.restoreSession().subscribe();
    const request = http.expectOne(`${API}/auth/me`);
    expect(request.request.headers.get('Authorization')).toBe('Bearer access-1');
    request.flush(fakeUser);
    expect(auth.user()).toEqual(fakeUser);
  });

  it('logout borra tokens y usuario y va al login', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    storage.save(fakeTokens);
    auth.setUser(fakeUser);
    auth.logout();
    expect(storage.accessToken).toBeNull();
    expect(auth.isLoggedIn()).toBe(false);
    expect(navigate).toHaveBeenCalledWith('/login');
  });
});
