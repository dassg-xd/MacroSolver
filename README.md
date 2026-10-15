# Documentación del Proyecto: MacroSolver
**Aplicación de Métodos Numéricos para el Modelado Dinámico del Gasto Calórico y Seguimiento Nutricional**

---

## 1. Introducción y Justificación
**MacroSolver** es una aplicación web diseñada para resolver un problema físico y fisiológico complejo: la pérdida de peso no es un proceso lineal. A medida que el cuerpo humano pierde masa, su Tasa Metabólica Basal (TMB) disminuye, provocando una "adaptación metabólica" que reduce el déficit calórico real con el paso del tiempo.

Los enfoques nutricionales tradicionales asumen un gasto calórico estático, lo que genera estancamientos y proyecciones erróneas. Para solucionar esto, MacroSolver abandona el álgebra básica y emplea **Métodos Numéricos** para simular día a día el comportamiento metabólico, calcular ingestas exactas mediante búsqueda de raíces y ajustar proyecciones a la realidad física mediante análisis de regresión. 

## 2. Arquitectura de Desarrollo
El proyecto está estructurado como una aplicación web moderna, escalable y orientada al procesamiento de datos:
*   **Backend:** Java con el framework Spring Boot.
*   **Base de Datos:** PostgreSQL alojada en Supabase, utilizando Prisma ORM para el modelado de datos.
*   **Lógica de Negocio:** Implementación nativa de algoritmos numéricos en Java para el procesamiento de la simulación diaria.

## 3. Modelado Fisiológico (Ecuaciones Base)
Antes de aplicar los métodos numéricos, el sistema se fundamenta en las siguientes ecuaciones biológicas que se evaluarán iterativamente:

*   **Tasa Metabólica Basal (Ecuación de Mifflin-St Jeor):**
    Determina las calorías quemadas en reposo en función del peso actual ($W$ en kg), altura ($H$ en cm) y edad ($E$ en años).
    Para hombres: $$TMB = (10 \cdot W) + (6.25 \cdot H) - (5 \cdot E) + 5$$
    Para mujeres: $$TMB = (10 \cdot W) + (6.25 \cdot H) - (5 \cdot E) - 161$$

*   **Gasto Energético Total Diario (TDEE):**
    $$TDEE(W) = TMB(W) \cdot \text{Factor de Actividad}$$

*   **Distribución de Macronutrientes:**
    Proteínas = $2 \cdot W$ gramos.
    Grasas = $(0.25 \cdot \text{Calorías}) / 9$ gramos.
    Carbohidratos = $(\text{Calorías} - (\text{Proteínas} \cdot 4) - (\text{Grasas} \cdot 9)) / 4$ gramos.

---

## 4. Núcleo Matemático: Implementación de Métodos Numéricos
Los métodos numéricos constituyen el motor del software. El sistema funciona calculando tres curvas distintas que interactúan entre sí:

### 4.1. Método de Euler (Simulación de la Curva Diaria)
**Propósito:** Resolver la ecuación diferencial del cambio de peso corporal a lo largo del tiempo. Dado que el TDEE cambia al perder peso, se utiliza el Método de Euler para proyectar el peso día por día.

**Implementación:**
La tasa de cambio de peso depende de la diferencia entre lo que el usuario come (Ingesta) y lo que gasta (TDEE). Sabiendo que 7700 kcal equivalen a 1 kg, la ecuación iterativa diaria (con un paso $h = 1$ día) es:

$$W_{i+1} = W_i + \frac{\text{Ingesta} - TDEE(W_i)}{7700}$$

**Aplicación en el sistema:**
*   **Curva Ideal Teórica:** Se evalúa Euler asumiendo que el usuario cumple la ingesta recomendada al 100%.
*   **Curva de Simulación por Adherencia:** Se re-evalúa Euler reemplazando la variable `Ingesta` por las **calorías reales consumidas** ingresadas por el usuario diariamente. Esto permite ver el impacto real de desviaciones en la dieta, calculando el retraso o adelanto hacia la meta.

### 4.2. Método de la Secante (Búsqueda de Raíces para la Meta)
**Propósito:** Encontrar la cantidad exacta de calorías (la meta) que el usuario debe consumir diariamente para llegar a su peso objetivo en un tiempo definido (ej. 60 días). 

**Implementación:**
Debido a la adaptación metabólica simulada por Euler, no existe una fórmula directa para despejar las calorías. Se define una función de error $f(x)$, donde $x$ son las calorías diarias a probar, y $f(x)$ es el peso final simulado en el día 60 menos el peso objetivo.

$$x_{n+1} = x_n - f(x_n) \frac{x_n - x_{n-1}}{f(x_n) - f(x_{n-1})}$$

El algoritmo asume dos ingestas iniciales (ej. 2000 y 1500 kcal), simula los 60 días con Euler, e itera usando la fórmula de la Secante hasta que el error sea cero ($f(x) \approx 0$). El valor resultante es la recomendación calórica del sistema.

### 4.3. Mínimos Cuadrados (Regresión Exponencial para la Curva Física)
**Propósito:** Ajustar las predicciones teóricas a la realidad fisiológica. El usuario registra su peso real semanalmente. Debido a fluctuaciones, se ajusta una curva exponencial que represente la tendencia real de pérdida.

**Implementación:**
Asumiendo un modelo $y = C \cdot e^{Ax}$, se linealiza aplicando logaritmo natural ($\ln y = \ln C + Ax$). Para un conjunto de $n$ registros reales $(x_i, y_i)$, se calculan los coeficientes:

$$A = \frac{n \sum_{i=1}^n (x_i \ln y_i) - \sum_{i=1}^n x_i \sum_{i=1}^n \ln y_i}{n \sum_{i=1}^n x_i^2 - \left(\sum_{i=1}^n x_i\right)^2}$$

$$a_0 = \frac{\sum_{i=1}^n \ln y_i - A \sum_{i=1}^n x_i}{n}$$

Donde $C = e^{a_0}$. La nueva curva predictiva es $Peso(x) = C \cdot e^{A \cdot x}$.

---

## 5. Flujo Lógico de Ejecución y Tolerancia al Comportamiento Humano
El diseño del software permite retroalimentación constante:
1.  **Planeación:** El sistema usa la *Secante* para definir la Ingesta Teórica, y grafica la trayectoria ideal usando *Euler*.
2.  **Seguimiento de Adherencia:** El usuario ingresa sus calorías reales diarias. El sistema recalcula la trayectoria con *Euler* basándose en sus acciones reales.
3.  **Seguimiento Físico:** El usuario ingresa su peso real semanal. El sistema aplica *Mínimos Cuadrados* para generar la curva de tendencia real.
4.  **Re-Planeación (Corrección de Rumbo):** Si la tendencia real de Mínimos Cuadrados difiere significativamente del Peso Objetivo para el Día 60, el sistema reinicia el ciclo. Toma el peso actual real, ajusta el tiempo restante, y vuelve a utilizar la *Secante* para generar una nueva recomendación calórica, completamente adaptada a la realidad metabólica actual del usuario.
