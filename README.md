# MacroSolver

MacroSolver es una plataforma web orientada a la planificación nutricional y pérdida de grasa de forma gradual y medible en personas adultas. A diferencia de las calculadoras convencionales que asumen un gasto calórico constante, MacroSolver implementa un **modelo dinámico de composición corporal** mediante métodos numéricos. El sistema contempla la adaptación metabólica (reducción del gasto energético a medida que disminuye la masa corporal) para determinar ingestas calóricas viables, evaluar desviaciones diarias y re-ajustar la planificación con base en los pesos reales del usuario.

---

## Funcionalidades Principales

* **Estimación de Composición Corporal:** Determina la masa grasa inicial ($F$) y la masa libre de grasa ($L$) mediante mediciones antropométricas (circunferencias) o estimaciones por $IMC$, edad y sexo.
* **Verificación de Viabilidad:** Evalúa la factibilidad de la meta fijada mediante la simulación de escenarios ideales con límite de déficit calórico seguro ($700 \text{ kcal/día}$ o ajuste por piso metabólico). Si la fecha meta no es posible, calcula la fecha mínima viable.
* **Seguimiento Diario y Desviaciones:** Registro de calorías e ingesta diaria en un calendario interactivo. Las desviaciones en la ingesta simulan el impacto directo sobre la fecha de llegada proyectada.
* **Análisis de Tendencia y Proyección:** Proyección de tendencia mediante ajuste de datos de peso real por Mínimos Cuadrados, mitigando las fluctuaciones de peso a corto plazo.
* **Sugerencia de Re-planeación:** Monitoreo constante que sugiere un nuevo plan de ajuste cuando el progreso real se desvía de la tolerancia definida.
* **Transparencia en el Cálculo:** Pantalla explicativa con el detalle de las iteraciones del método numérico, análisis de sensibilidad y métricas de error.

---

## Fundamento Numérico y Modelo Matemático

El motor numérico aplica un modelo dinámico de dos compartimentos (masa grasa $F$ y masa libre de grasa $L$, con peso total $W = F + L$). La variación de peso distribuye la pérdida energética mediante una relación de masa dependiente de la adiposidad actual $p(F)$:

$$B = I - \text{TDEE}(W)$$

$$p(F) = \frac{C}{C + F}, \quad \text{donde } C = 10.4 \cdot \frac{\rho_L}{\rho_F}$$

$$\frac{dF}{dt} = \frac{(1 - p) \cdot B}{\rho_F}$$

$$\frac{dL}{dt} = \frac{p \cdot B}{\rho_L}$$

Donde:
* $I$: Ingesta calórica diaria ($\text{kcal/día}$).
* $\text{TDEE}(W)$: Gasto energético diario total en función del peso ($\text{kcal/día}$).
* $\rho_F = 9400 \text{ kcal/kg}$: Densidad energética de la masa grasa.
* $\rho_L = 1800 \text{ kcal/kg}$: Densidad energética de la masa libre de grasa.

El modelo garantiza la conservación de la energía:

$$\rho_F \cdot \Delta F + \rho_L \cdot \Delta L = \sum B$$

### Métodos Numéricos Utilizados

1. **Método de Euler:** Integra las ecuaciones diferenciales del sistema día a día ($h = 1 \text{ día}$) para obtener las curvas proyectadas de $F$, $L$ y $W$.
2. **Runge-Kutta de Orden 4 (RK4):** Utilizado como solución de referencia de alta precisión para verificar la convergencia y estimar el error de integración.
3. **Método de la Secante:** Encuentra la ingesta exacta $I$ resolviendo la raíz de la función objetivo $f(I) = W(N; I) - W_{\text{meta}}$ en la fecha objetivo.
4. **Mínimos Cuadrados (Regresión Exponencial):** Realiza un ajuste de curva $y = C \cdot e^{A \cdot x}$ sobre el historial de pesos reales para proyectar el ritmo efectivo de pérdida de peso.

---

## Tecnologías Utilizadas

* **Frontend:** React, TypeScript, Vite, Recharts.
* **Backend:** Python, FastAPI, Pydantic, Supabase.
* **Base de Datos:** PostgreSQL en Supabase.
* **Autenticación:** JWT (JSON Web Tokens) y hashing de contraseñas con BCrypt.

---

## Puntos de Enlace de la API (Endpoints)

| Sección | Método | Ruta | Descripción |
| --- | --- | --- | --- |
| **Autenticación** | `POST` | `/auth/registro` | Registro de nuevos usuarios |
| | `POST` | `/auth/login` | Inicio de sesión y obtención de token |
| **Perfil** | `GET` / `PATCH` | `/me` | Consulta y actualización de datos de usuario |
| **Planes** | `POST` | `/plans/estimar-composicion` | Cálculo aproximado de masa grasa y magra |
| | `POST` | `/plans/preview` | Vista previa, simulación y viabilidad de meta |
| | `POST` | `/plans` | Confirmación y activación de un plan |
| | `GET` | `/plans/active` | Obtención del plan actualmente activo |
| | `GET` | `/plans` | Historial de planes del usuario, del más reciente al más antiguo |
| **Seguimiento** | `PUT` | `/plans/active/calorias` | Registro diario de calorías (`{fecha, kcal}`; `kcal: null` lo borra) |
| | `PUT` | `/plans/active/pesos` | Registro diario de peso (`{fecha, peso_kg}`; `null` lo borra) |
| | `PUT` | `/plans/active/actividades` | Reemplaza las actividades del día (`{fecha, actividades: [{actividad_id, minutos}]}`) |
| | `GET` | `/actividades` | Catálogo de actividades físicas con su MET |
| | `GET` | `/plans/active/calendario?mes=AAAA-MM` | Días del mes con estado, registros y cumplimiento (±10 %) |
| | `GET` | `/plans/active/seguimiento` | Curva ideal, curva por adherencia, pesos reales, tendencia, llegada estimada y sugerencia de re-planeación |
| | `POST` | `/plans/active/replanear/preview` | Plan propuesto junto al actual, sin guardar (`{fecha_meta}` opcional para aceptar la fecha viable) |
| | `POST` | `/plans/active/replanear` | Crea el plan encadenado; el anterior queda inactivo |
| | `GET` | `/plans/active/estadisticas` | Adherencia, peso promedio y ejercicio por semana (domingo a sábado) |
| | `GET` | `/guias?comidas=4` | Macros del plan repartidos en 3, 4 o 5 comidas y consejos |
| | `GET` | `/plans/active/calculo` | Reporte técnico de iteraciones y sensibilidad |
| **Salud del Sistema**| `GET` | `/health` | Verificación de estado de la API |

---

## Instalación y Configuración Local

### Requisitos Previos

* Python 3.13.17+
* Node.js 24.19.0+

### Base de datos (Supabase)

En el SQL Editor del proyecto, ejecutar en orden los scripts de `backend/sql`:

1. `01_verificar_esquema-v0.03.sql` (solo lectura: muestra restricciones, índices, triggers y RLS).
2. `02_corregir_esquema-v0.03.sql`
3. `03_plan_v0.04.sql` (columnas de composición y la función `crear_plan`).
4. `04_permitir_plan_inactivo.sql`

### Configuración del Backend

1. Entrar a la carpeta del backend y crear el entorno virtual:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copiar `backend/.env.example` como `backend/.env` y completar:
   ```env
   SUPABASE_URL=https://TU_PROYECTO.supabase.co
   SUPABASE_SECRET_KEY=sb_secret_...        # Settings > API Keys > Secret
   JWT_SECRET=un-texto-de-32-caracteres-o-mas
   JWT_EXPIRATION_MINUTES=1440
   CORS_ORIGINS=http://localhost:5173
   ```

3. Iniciar el servidor (con el entorno activado, desde `backend/`):
   ```bash
   uvicorn app.main:app --reload
   ```
   También sirve ejecutar `backend/app/main.py` directamente (botón ▶ de VS Code): arranca
   uvicorn con el Python de `backend/.venv`.

4. Comprobar: http://127.0.0.1:8000/docs muestra los endpoints y
   http://127.0.0.1:8000/health responde `"ok": true` si hay conexión con Supabase.

### Configuración del Frontend

1. Copiar `frontend/.env.example` como `frontend/.env`. Sin este archivo el frontend no
   encuentra el backend:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

2. En otra terminal, instalar las dependencias e iniciar:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Abrir http://localhost:5173. El backend y el frontend deben quedar corriendo a la vez.

---

## Ejecución de Pruebas Automáticas

```bash
cd backend
pytest
```

Las pruebas no usan la red ni la base de datos:

* **Motor numérico:** validaciones V1 a V8 (orden de Euler frente a RK4, Secante frente a
  bisección, regresión, conservación de energía, sensibilidad, convención de índices y plazo
  mínimo), las 6 pruebas de la beta y la relación grasa-peso de Forbes.
* **API:** sesión, registro, planes, registros diarios, calendario, seguimiento, re-planeación,
  estadísticas, historial y guía, con repositorios en memoria.

Para revisar el frontend:

```bash
cd frontend
npm run build
npm run lint
```

---

## Descargo de Responsabilidad

MacroSolver es una herramienta de estimación matemática orientada a adultos sanos mayores de 18 años. El sistema utiliza modelos numéricos aproximados y no constituye un diagnóstico, tratamiento ni asesoría médica profesional. No está diseñado para mujeres embarazadas ni para personas con condiciones médicas que requieran supervisión especializada.
