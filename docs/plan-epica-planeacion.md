# Plan de implementación · Épica 2 (Planeación) y cierre de Épica 1

**Versión:** 1.0 · **Fecha:** 5 de noviembre de 2026 · **Rama:** `feature/epic/planeacion`

Este documento registra las decisiones aprobadas y el orden de implementación. La fuente
funcional sigue siendo el *Documento de software v0.5*.

## Decisiones aprobadas

| Tema | Decisión |
| --- | --- |
| Historias nuevas de Épica 1 | Se aprueban HU-01A, HU-02A, HU-02B, HU-04A, HU-04B y HU-04C; se amplía HU-03 |
| Mensaje de login | Genérico: «Correo o contraseña incorrectos.» |
| Historial de planes | No se implementa en esta entrega; no aparece en la navegación |
| Bloqueos de vista previa | La vista previa responde `200` con `puede_confirmar: false` y la lista de bloqueos |
| «Cómo se calculó» | Componente reutilizable, embebido en la vista previa y con pantalla propia |
| Panel | Panel mínimo con el plan activo; el panel completo es de la Épica 3 |
| Fecha de inicio | Por defecto hoy; editable con restricciones (no futura, meta futura, plazo entre 2 y 730 días) |
| JWT | 24 horas (1440 minutos) |
| Recharts | Se instala y se revisan vulnerabilidades con `npm audit` |
| `.env.example` | Se restaura en `backend/` y `frontend/` |

## Orden de commits

1. `docs: plan de la épica 2 y documento de software v0.5`
2. `chore: restaurar .env.example y ampliar el JWT a 24 horas`
3. `feat(auth): sesión persistente, rutas protegidas y cierre de sesión`
4. `feat(perfil): edición de perfil con PATCH /me`
5. `feat(plan): migración, RPC transaccional y endpoints de planeación`
6. `feat(plan): pantalla de nuevo plan, vista previa y cómo se calculó`
7. `feat(panel): panel mínimo y bienvenida al primer plan`
8. `docs: actualizar README, CHANGELOG y evidencias de la semana`

## Fase 0 · Preparación

- Verificar el esquema real de Supabase con `backend/sql/01_verificar_esquema-v0.03.sql`.
- Confirmar que `fecha_meta` y `activo` son columnas generadas.
- Instalar `pytest` en `backend/.venv` y correr la suite base (80 pruebas).
- Mantener los cambios locales de `backend/app/services/configuracion.py`.

## Fase 1 · Cierre de Épica 1

### Backend

- `PATCH /me` con validación de nombre, sexo, fecha de nacimiento, altura, factor de
  actividad y nivel de entrenamiento.
- Validación de contraseña con al menos una letra y un número.
- Bloqueo temporal de 3 intentos fallidos durante 15 minutos.
- JWT de 24 horas.
- Pruebas de perfil, contraseña y bloqueo.

### Frontend

- `SessionProvider` con token, usuario, login, registro, logout y actualización de perfil.
- `RutaProtegida` con retorno a la pantalla solicitada.
- Layout con barra de navegación, chip de usuario, menú y aviso de salud.
- Modal de cierre de sesión y avisos de sesión cerrada/expirada.
- Pantalla de bienvenida posterior al registro.
- Pantalla de perfil editable.

## Fase 2 · Backend de planeación

### Endpoints

| Método | Ruta | Historia |
| --- | --- | --- |
| `POST` | `/plans/estimar-composicion` | HU-06 |
| `POST` | `/plans/preview` | HU-05, HU-06, HU-07, HU-08, HU-09 |
| `POST` | `/plans` | HU-05 |
| `GET` | `/plans/active` | HU-05 |
| `GET` | `/plans/active/calculo` | HU-09 |

### Reglas

- `N = fecha_meta - fecha_inicio` (días); la curva va del día 0 al día N.
- El perfil se copia del usuario al crear el plan: sexo, edad, altura y factor de actividad.
- La composición se estima con Marina; si faltan medidas, con Deurenberg.
- La confirmación recalcula en servidor y nunca confía en la vista previa.
- La confirmación usa la función PostgreSQL `crear_plan` para desactivar el plan anterior e
  insertar el nuevo en una sola transacción.
- Bloqueos: meta no es pérdida, IMC de la meta menor que 18.5, plazo no viable, meta
  inalcanzable en 180 días.

### Archivos

- `backend/app/schemas/plan.py`
- `backend/app/repositories/plan_repository.py`
- `backend/app/services/plan_service.py`
- `backend/app/routes/planes.py`
- `backend/sql/03_plan_v0.04.sql`
- `backend/tests/test_plan_schemas.py`
- `backend/tests/test_plan_service.py`
- `backend/tests/test_api_planes.py`
- `backend/tests/test_api_calculo.py`

## Fase 3 · Frontend de planeación

- Ruta `/nuevo-plan` con formulario y vista previa en dos columnas.
- Campos: peso inicial, peso meta, fecha inicio, fecha meta, cuello, cintura y cadera
  (solo mujeres).
- Tarjetas: viabilidad, ingesta, composición, macros, pérdida estimada, sensibilidad.
- Gráfica Recharts con curva ideal, banda de tolerancia y línea de meta.
- Tabla de iteraciones de la Secante.
- Bloqueos y advertencias visibles antes de confirmar.
- CTA para usar la fecha viable cuando la fecha pedida no alcance.
- Ruta `/plan/como-se-calculo` y componente embebido.
- Ruta `/panel` con resumen mínimo del plan activo.
- Ruta `/perfil` y `/bienvenida`.

## Fase 4 · Pruebas y cierre

- Backend: esquemas, servicio, endpoints, cálculo y rendimiento.
- Frontend: `npm run build`, `npm run lint` y pruebas manuales guiadas por mockups.
- Actualizar `README.md`, `CHANGELOG.md` y `docs/evidencias/semana2/`.
- Revisar `npm audit` después de instalar Recharts.

## Mockups usados

- **3 · Nuevo plan**: pantalla principal de la épica.
- **22 · Cuenta lista**: onboarding.
- **1 · Panel**: destino y resumen mínimo.
- **8 · Panel móvil**: referencia responsive.
- **2 · Mi perfil**: perfil y chip de usuario.
- **23 · Cerrar sesión**: modal.
- **9–21 y 24–26**: estados de autenticación.

## Mockups pendientes

- Estado de meta no viable con fecha viable e ingesta.
- Estados de meta inalcanzable, IMC bajo, meta no es pérdida y medidas inválidas.
- Composición estimada por respaldo IMC.
- Pérdida estimada ΔF/ΔL y banda de tolerancia.
- Confirmación exitosa del plan.
- “Cómo se calculó” como pantalla completa.
- Estados de carga y error.
- Nuevo plan en móvil.
- Panel sin plan activo.
- Aviso de salud.
- Error de servidor o sin conexión.

Mientras no existan, se implementan estados provisionales con el mismo sistema visual y se
documentan en este archivo.
