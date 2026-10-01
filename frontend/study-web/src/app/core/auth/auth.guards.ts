import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Solo usuarios con sesión; si no, al login recordando a dónde quería ir. */
export const authGuard: CanActivateFn = (_route, state) => {
  if (inject(AuthService).isLoggedIn()) {
    return true;
  }
  return inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

/** Login y registro: si ya hay sesión no tiene sentido mostrarlos. */
export const guestGuard: CanActivateFn = () => {
  return inject(AuthService).isLoggedIn() ? inject(Router).createUrlTree(['/']) : true;
};

/** Solo administradores. Se usa debajo de authGuard. */
export const adminGuard: CanActivateFn = () => {
  return inject(AuthService).isAdmin() ? true : inject(Router).createUrlTree(['/']);
};
