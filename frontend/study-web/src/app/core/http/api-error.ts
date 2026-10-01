import { HttpErrorResponse } from '@angular/common/http';

/** Convierte un error del backend en un mensaje para mostrar al usuario. */
export function apiErrorMessage(error: unknown, fallback = 'Ocurrió un error inesperado'): string {
  if (!(error instanceof HttpErrorResponse)) {
    return fallback;
  }
  if (error.status === 0) {
    return 'No se pudo conectar con el servidor. ¿Está levantado el backend?';
  }
  // FastAPI devuelve {detail: "mensaje"}; en errores 422 detail es una lista
  const detail = error.error?.detail;
  return typeof detail === 'string' ? detail : fallback;
}
