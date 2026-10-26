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
| **Autenticación** | `POST` | `/auth/register` | Registro de nuevos usuarios |
| | `POST` | `/auth/login` | Inicio de sesión y obtención de token |
| **Perfil** | `GET` / `PATCH` | `/me` | Consulta y actualización de datos de usuario |
| **Planes** | `POST` | `/plans/estimar-composicion` | Cálculo aproximado de masa grasa y magra |
| | `POST` | `/plans/preview` | Vista previa, simulación y viabilidad de meta |
| | `POST` | `/plans` | Confirmación y activación de un plan |
| | `GET` | `/plans/active` | Obtención del plan actualmente activo |
| **Seguimiento** | `PUT` | `/plans/active/calorias` | Registro diario de calorías |
| | `PUT` | `/plans/active/pesos` | Registro diario de peso corporal |
| | `GET` | `/plans/active/calendario` | Datos agregados del mes |
| | `GET` | `/plans/active/seguimiento` | Curvas simuladas, tendencia y proyección |
| | `POST` | `/plans/active/replanear` | Generación de nuevo plan por re-planeación |
| | `GET` | `/plans/active/estadisticas` | Indicadores de adherencia y variaciones semanales |
| | `GET` | `/plans/active/calculo` | Reporte técnico de iteraciones y sensibilidad |
| **Salud del Sistema**| `GET` | `/health` | Verificación de estado de la API |

---

## Instalación y Configuración Local

### Requisitos Previos

* Python 3.13.17+
* Node.js 24.19.0+

### Configuración del Backend

1. Clonar el repositorio y acceder al directorio del backend:
   ```bash
   cd backend
   ```

2. Crear y activar el entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar las variables de entorno creando un archivo `.env`:
   ```env
   DATABASE_URL=postgresql://usuario:password@localhost:5432/macrosolver
   JWT_SECRET=tu_clave_secreta
   ```

5. Iniciar el servidor de desarrollo:
   ```bash
   uvicorn app.main:app --reload
   ```

### Configuración del Frontend

1. Acceder al directorio del frontend:
   ```bash
   cd frontend
   ```

2. Instalar las dependencias de Node:
   ```bash
   npm install
   ```

3. Iniciar el servidor de desarrollo:
   ```bash
   npm run dev
   ```

---

## Ejecución de Pruebas Automáticas

Para validar la convergencia de los métodos numéricos (V1 a V6) y las pruebas de los endpoints:

```bash
cd backend
pytest
```

---

## Descargo de Responsabilidad

MacroSolver es una herramienta de estimación matemática orientada a adultos sanos mayores de 18 años. El sistema utiliza modelos numéricos aproximados y no constituye un diagnóstico, tratamiento ni asesoría médica profesional. No está diseñado para mujeres embarazadas ni para personas con condiciones médicas que requieran supervisión especializada.
