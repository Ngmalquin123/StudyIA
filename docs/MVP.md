# StudyIA — Definición del MVP

> **Fase 1 del plan de desarrollo**
> Documento de alcance. Define **qué entra** y **qué no entra** en la primera versión.
> Última actualización: 28 de septiembre de 2026

---

## 1. Propósito

Este documento existe para evitar el problema más común en proyectos de software: **que crezcan sin control**.

Cada función que se agrega tiene un costo (tiempo, complejidad, más cosas que pueden fallar). Este documento fija la frontera: lo que está adentro se entrega completo, lo que está afuera se anota como ampliación.

**Regla de oro:** si una función no está en la sección 2, **no se implementa** hasta que el MVP esté terminado y probado.

---

## 2. El MVP en una frase

> Un estudiante se registra, organiza sus materias y temas, responde preguntas de opción múltiple, ve su progreso, y consulta a una IA que le explica temas, le genera preguntas y le recomienda qué repasar.

---

## 3. Funciones dentro del MVP

### 3.1 Cuentas y acceso

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 1.1 | Registro | El estudiante crea su cuenta con nombre, email y contraseña | Alta |
| 1.2 | Login | Ingresa con email y contraseña, recibe un token JWT | Alta |
| 1.3 | Sesión persistente | El token se guarda en el navegador y evita volver a iniciar sesión | Alta |
| 1.4 | Aislamiento de datos | Cada estudiante ve **solo** su propia información | Alta |
| 1.5 | Contraseñas seguras | Se guardan hasheadas con bcrypt, nunca en texto plano | Alta |

> **Por qué el punto 1.4 importa:** es un requisito de seguridad, no una comodidad. Si el estudiante A pudiera ver los datos del estudiante B, el proyecto no es presentable.

### 3.2 Contenido académico

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 2.1 | Materias (CRUD) | Crear, listar, editar y eliminar materias del estudiante | Alta |
| 2.2 | Temas (CRUD) | Crear, listar, editar y eliminar temas dentro de una materia | Alta |
| 2.3 | Preguntas (CRUD) | Crear preguntas de opción múltiple con sus opciones | Alta |
| 2.4 | Preguntas por IA | El estudiante pide que la IA genere preguntas de un tema y decide si las guarda | Media |

### 3.3 Práctica y evaluación

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 3.1 | Responder | Responder las preguntas de un tema | Alta |
| 3.2 | Corrección en el servidor | El **backend** corrige; el frontend nunca envía si acertó o falló | Alta |
| 3.3 | Feedback inmediato | Al responder, saber si es correcto o incorrecto | Media |
| 3.4 | Resultado del intento | Ver porcentaje de aciertos al terminar | Alta |
| 3.5 | Historial | Ver los intentos anteriores | Media |

> **Por qué el punto 3.2 es no negociable:** si el navegador dijera "acertaste", un estudiante podría hacer trampa viendo el código. La corrección tiene que ocurrir en el servidor, donde el estudiante no llega.

### 3.4 Progreso

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 4.1 | Porcentaje de aciertos | `correctas / total × 100` | Alta |
| 4.2 | Progreso por tema | Acumulado de todos los intentos de un tema | Alta |
| 4.3 | Tema fuerte / débil | Fuerte ≥ 70%, débil < 60% | Media |
| 4.4 | Dashboard | Visualización del progreso del estudiante | Media |

### 3.5 Inteligencia Artificial

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 5.1 | Chat | Conversación con la IA sobre sus materias | Alta |
| 5.2 | Explicar un tema | Explicación en 3 niveles: simple, intermedio, avanzado | Alta |
| 5.3 | Resumir un texto | Resumen a partir de texto pegado | Media |
| 5.4 | Generar preguntas | Devuelve preguntas con sus 4 opciones, revisables antes de guardar | Media |
| 5.5 | Manejo de errores | Si la IA falla o se agota el límite, el mensaje es claro, no una caída | Alta |

### 3.6 Recomendaciones

| # | Función | Descripción | Prioridad |
|---|---------|-------------|-----------|
| 6.1 | Regla de debilidad | Si el % de aciertos de un tema es < 60%, se recomienda repasar | Alta |
| 6.2 | Motivo explicable | Cada recomendación dice **por qué** se hace, en texto | Alta |
| 6.3 | Marcar como visto | El estudiante puede descartar una recomendación | Baja |

---

## 4. Funciones fuera del MVP (ampliación)

Estas **no** se hacen ahora. Anotadas para planning futuro:

| # | Función | Por qué fuera del MVP |
|---|---------|----------------------|
| F1 | Carga de PDFs | Requiere almacenamiento de archivos y extracción de texto |
| F2 | RAG (preguntar sobre documentos) | Depende de F1. Es la fase más compleja del proyecto |
| F3 | Embeddings + base vectorial | Solo tiene sentido con RAG |
| F4 | Machine Learning para recomendaciones | Necesita miles de datos de estudiantes que no tenemos |
| F5 | Panel de profesores | El MVP es de un solo tipo de usuario |
| F6 | Notificaciones | No es necesario para demostrar nada |
| F7 | Aplicación móvil | Otro proyecto entero |
| F8 | Gamificación | Decorativo, no aporta al objetivo académico |
| F9 | Despliegue en la nube | Se hace al final, para la presentación |
| F10 | Historial avanzado de conversaciones | El MVP guarda la sesión actual |

---

## 5. Criterio de "terminado"

Una función está terminada cuando se cumplen **las cinco** condiciones:

1. ✅ Funciona (el usuario logra lo que se supone que debe lograr)
2. ✅ Es visible (hay una pantalla o un endpoint donde se puede ver, no es código invisible)
3. ✅ Guarda los datos (lo que tiene que persistir, persiste)
4. ✅ Valida errores (no revienta si el usuario mete datos malos)
5. ✅ Otras 2 personas del equipo pueden probarla siguiendo el README

**Sin las 5, la función no está terminada.** Punto 5 es el que más se olvida y el que más problemas causa en la entrega final.

---

## 6. Decisiones técnicas del MVP

### 6.1 Stack

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | Angular | 22.2 |
| Lenguaje | TypeScript | ~6.0 |
| Backend | FastAPI + Python | 3.14 |
| Base de datos | PostgreSQL | 18.3 |
| ORM | SQLAlchemy | 2.1 |
| Migraciones | Alembic | 1.20 |
| Autenticación | JWT (HS256) + bcrypt | — |
| IA | Gemini / OpenCode Zen | — |

### 6.2 Proveedor de IA intercambiable

El MVP usa **dos proveedores de IA** conmutables por configuración:

```env
IA_PROVEEDOR=gemini    # o "opencode"
```

Razón: los modelos gratuitos de OpenCode son *"for a limited time"* y pueden desaparecer. Con dos proveedores, si uno falla en la presentación, se cambia **una línea del `.env`** y la app sigue funcionando.

**Ninguna otra parte del código sabe qué proveedor se está usando.** Solo `ai_service.py` lo sabe. Esa es la única razón por la que la app no se rompe si mañana cambia el proveedor.

### 6.3 Reglas, no Machine Learning

Las recomendaciones del MVP se calculan con **reglas if/then**, no con ML.

Razón: para que un modelo de ML dé resultados útiles hacen falta miles de datos de estudiantes. No existen. Las reglas dan el 90% del resultado con el 2% del esfuerzo, y **son explicables** ante un profesor, lo que un modelo entrenado con 50 datos no sería.

La tabla de recomendaciones está diseñada para que un modelo de ML se pueda añadir después sin cambiar el esquema.

### 6.4 Dónde entra la IA y dónde no

| Función | ¿Usa IA? | Tecnología real |
|---------|-----------|-----------------|
| Login | **No** | FastAPI + PostgreSQL + JWT |
| Materias y temas | **No** | CRUD normal |
| Registrar respuestas | **No** | Datos estructurados |
| Calcular porcentaje | **No** | Algoritmo matemático en Python |
| Detectar debilidad | **No** | Reglas sobre resultados |
| Chat | **Sí** | LLM |
| Explicar tema | **Sí** | LLM |
| Resumir texto | **Sí** | LLM |
| Generar preguntas | **Sí** | LLM |
| Preguntar sobre PDFs | **Sí** | RAG (fuera del MVP) |

> **Esto es importante para la defensa.** La IA no controla el sistema: es **una** pieza entre varias. El 70% de StudyIA funciona perfectamente sin ninguna IA. Eso es una decisión de diseño, no una limitación.

### 6.5 Seguridad

| Medida | Detalle |
|--------|---------|
| Usuario de BD dedicado | Rol `studyia`, **no** superusuario. Daño acotado a la base `studyia` |
| Contraseñas | Hasheadas con bcrypt, nunca reversibles |
| Secretos | Fuera del código, en `.env`, que Git ignora |
| Aislamiento por usuario | Cada endpoint filtra por `user_id` del token |
| CORS | Solo `localhost:4200` permitido |

---

## 7. Reparto de responsabilidades

| Integrante | Rol | Fases |
|-----------|-----|-------|
| Integrante 1 | Frontend | 6, 7, 8 + apoyo en 12 |
| Integrante 2 | Backend + BD | 3, 4, 5, 7, 8 + apoyo en 12 |
| Integrante 3 | IA + recomendaciones | 9, 10, 11 + apoyo en 12 |

> **Nota sobre la colaboracion:** como los tres trabajan en la misma Mac y sobre la misma base de datos, las **migraciones de Alembic se ejecutan una sola vez** por quien esté tocando el esquema. Los demás solo levantan el backend. Ejecutarlas en paralelo genera conflictos.

---

## 8. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Modelos gratuitos de IA desaparecen | Alto | Ya mitigado: hay dos proveedores conmutables |
| Se nos va el tiempo y no llegamos a la IA | Alto | El MVP sigue siendo útil sin IA (secciones 3.1-3.4, 3.6) |
| El alcance se infla con ideas nuevas | Medio | Este documento: lo que no está en §3 no se hace |
| Conflictos de migración en la BD compartida | Medio | Un solo responsable por vez para Alembic |
|Se filtra una API key | Medio | Revocar y regenerar desde el panel del proveedor |

---

## 9. Cómo saber si vamos bien

Al final de cada fase nos preguntamos:

- [ ] ¿Se puede **demostrar** en un computador, no solo decir que existe?
- [ ] ¿Las 3 personas del equipo pueden levantarlo siguiendo el README?
- [ ] ¿Hay datos de demostración para que la pantalla no se vea vacía?
- [ ] ¿Se rompió algo que antes funcionaba?

Si alguna respuesta es "no", esa fase no está cerrada y seguimos en ella.

---

## 10. Alcance temporal estimado

| Fase | Contenido | Horas |
|------|-----------|-------|
| 0 | Entorno (Node, BD, venv, keys) | 1 |
| 1 | Definir el MVP | 0.5 |
| 2 | Base de datos + modelos + Alembic | 2 |
| 3 | API CRUD | 2 |
| 4 | Autenticación JWT | 1.5 |
| 5 | Frontend base | 3 |
| 6 | Módulo académico | 2.5 |
| 7 | Progreso y dashboard | 2 |
| 8 | IA | 3 |
| 9 | Recomendaciones | 1.5 |
| 10 | RAG *(opcional)* | 4 |
| 11 | Tests, seeds, README | 2 |
| | **Total sin RAG** | **~21** |
