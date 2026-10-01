import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  RouterStateSnapshot,
  UrlTree,
  provideRouter,
} from '@angular/router';
import { adminGuard, authGuard, guestGuard } from './auth.guards';
import { AuthService } from './auth.service';
import { fakeUser } from './auth.testing';

function run(guard: CanActivateFn, url = '/') {
  return TestBed.runInInjectionContext(() =>
    guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
  );
}

describe('auth guards', () => {
  let auth: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    auth = TestBed.inject(AuthService);
  });

  it('authGuard manda al login con returnUrl si no hay sesión', () => {
    const result = run(authGuard, '/admin/usuarios') as UrlTree;
    expect(result.toString()).toBe('/login?returnUrl=%2Fadmin%2Fusuarios');
  });

  it('authGuard deja pasar con sesión', () => {
    auth.setUser(fakeUser);
    expect(run(authGuard)).toBe(true);
  });

  it('guestGuard saca del login a quien ya tiene sesión', () => {
    expect(run(guestGuard)).toBe(true);
    auth.setUser(fakeUser);
    expect((run(guestGuard) as UrlTree).toString()).toBe('/');
  });

  it('adminGuard solo deja pasar al admin', () => {
    auth.setUser(fakeUser);
    expect((run(adminGuard) as UrlTree).toString()).toBe('/');
    auth.setUser({ ...fakeUser, rol: 'admin' });
    expect(run(adminGuard)).toBe(true);
  });
});
