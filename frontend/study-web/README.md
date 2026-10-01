# StudyIA - Frontend

Angular 22 (componentes standalone, signals, sin zone.js). Usa Node de `.nvmrc` (`nvm use` en la raíz del repo).

## Puesta en marcha

Con el backend levantado en `http://localhost:8000` (ver `backend/README.md`):

```bash
npm install
npm start          # http://localhost:4200
npm test           # tests con Vitest
npm run build      # build de producción en dist/
```

La URL del backend está en `src/environments/environment.ts`.

## Estructura

```
src/app/
  app.config.ts          HttpClient + interceptor, router, restaurar sesión al arrancar
  app.routes.ts          Rutas y qué guard protege cada una
  core/
    auth/
      auth.service.ts      login, registro, refresh, logout; usuario actual como signal
      auth.interceptor.ts  agrega el Bearer y, si llega 401, refresca el token y reintenta
      auth.guards.ts       authGuard (con sesión), guestGuard (sin sesión), adminGuard
      token-storage.ts     guarda los tokens en localStorage
      auth.models.ts       tipos iguales a los schemas del backend
    http/api-error.ts      convierte errores del backend en mensajes
    users/users.service.ts llamadas a /api/users
  layout/shell/          barra superior de las páginas con sesión
  features/
    auth/login/          /login
    auth/register/       /registro
    home/                /           (requiere sesión)
    admin/users/         /admin/usuarios (solo admin)
```

## Cómo funciona la sesión

1. Login o registro → el backend devuelve `access_token` y `refresh_token`, que se guardan en `localStorage`.
2. Al abrir la app, `restoreSession()` llama a `/api/auth/me` con el token guardado; así recargar la página no cierra la sesión.
3. Cada petición a `/api` lleva `Authorization: Bearer <access_token>` (lo pone el interceptor).
4. Si el backend responde `401`, el interceptor pide tokens nuevos a `/api/auth/refresh` y repite la petición. Si el refresh también falla, se cierra la sesión y se va a `/login`.
5. Si alguien entra a una página protegida sin sesión, `authGuard` lo manda a `/login?returnUrl=...` y después del login vuelve a donde quería ir.

Para agregar una página con sesión, ponla dentro de `children` de la ruta `''` en `app.routes.ts`.
