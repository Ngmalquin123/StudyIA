import { Routes } from '@angular/router';
import { adminGuard, authGuard, guestGuard } from './core/auth/auth.guards';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    title: 'Iniciar sesión · StudyIA',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'registro',
    canActivate: [guestGuard],
    title: 'Crear cuenta · StudyIA',
    loadComponent: () => import('./features/auth/register/register').then((m) => m.Register),
  },
  {
    // Todo lo que está aquí dentro requiere sesión
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/shell/shell').then((m) => m.Shell),
    children: [
      {
        path: '',
        title: 'Inicio · StudyIA',
        loadComponent: () => import('./features/home/home').then((m) => m.Home),
      },
      {
        path: 'admin/usuarios',
        canActivate: [adminGuard],
        title: 'Usuarios · StudyIA',
        loadComponent: () =>
          import('./features/admin/users/admin-users').then((m) => m.AdminUsers),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
