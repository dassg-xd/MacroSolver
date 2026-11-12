# Plan de desarrollo · mejora de UX del frontend

**Alcance:** mejora incremental del frontend existente. No cambia contratos de API ni requiere cambios en el backend.  
**Base de análisis:** archivos actuales de `frontend/src`, configuración del frontend, rutas y esquemas del backend, `README.md` y los documentos presentes en `docs/`. El documento `.docx` se pudo leer extrayendo el texto de su XML interno; los diagramas ER y su copia de respaldo también se pudieron leer.

## 1. Producto y alcance

MacroSolver ayuda a personas adultas a planificar una pérdida de grasa gradual, medible y segura. En lugar de tratar el gasto calórico como constante, el backend modela su adaptación al peso; la interfaz debe ayudar a entender la estimación y su incertidumbre, registrar datos sin culpabilizar al usuario y mostrar cómo los registros afectan la meta. La herramienta no mide grasa, no diagnostica ni reemplaza a un profesional de la salud; el aviso ya existe en las pantallas de cuenta y el pie del layout. Fuentes: [README.md](../README.md), [Documento de software v0.5](./MacroSolver%20-%20Documento%20de%20software%20v0.5.docx), [plan de Épica 2](./plan-epica-planeacion.md).

Flujos actuales que deben conservarse:

1. Crear cuenta e iniciar sesión; completar perfil y cerrar sesión.
2. Definir meta, fechas y medidas; consultar viabilidad, bloqueos, macros, composición y curva antes de guardar el plan.
3. Registrar calorías, peso y actividades por día; revisar calendario, seguimiento, tendencia, estimación de llegada y sugerencia de re-planeación.
4. Ver estadísticas semanales, guía de nutrición, historial de planes y explicación del cálculo.

El backend entrega las series y resultados calculados; el frontend los presenta, no debe volver a implementar las fórmulas. Las rutas implementadas se conservan. Aunque el documento de software y el plan de Épica 2 dicen que Historial no se entrega o se retira de la navegación, el frontend actual sí ofrece `/historial`, el enlace de navegación y su integración con `GET /plans`; el plan de UX no lo elimina.

## 2. Inventario del frontend

### Rutas y pantallas

Todas las rutas salvo login y registro están bajo `RutaProtegida`; `/` y las rutas desconocidas redirigen a `/panel`. Fuente: [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), [RutaProtegida.tsx](../frontend/src/routes/RutaProtegida.tsx).

| Ruta | Pantalla | Función y estado actual |
|---|---|---|
| `/login` | Inicio de sesión | Credenciales, visibilidad de contraseña, carga, error y enlace a registro. |
| `/registro` | Registro | Formulario en dos pasos con datos de cuenta y perfil, requisitos de contraseña y validación. |
| `/panel` | Panel / bienvenida | Resumen del plan activo, métricas, curva y propuesta de re-planeación; si no hay plan, ofrece crear uno. |
| `/bienvenida` | Bienvenida | Confirma el registro y orienta a crear el primer plan. |
| `/perfil` | Perfil | Edición de nombre, sexo, fecha de nacimiento, altura, actividad y nivel de entrenamiento. |
| `/nuevo-plan` | Nuevo plan | Datos de meta y medidas, vista previa, bloqueos, advertencias, composición, macros, curva y explicación. |
| `/calendario` | Calendario | Cuadrícula mensual y edición del día seleccionado: calorías, peso y actividades. |
| `/estadisticas` | Estadísticas | Resumen semanal, gráfica de adherencia y tabla de peso, variación y ejercicio. |
| `/historial` | Historial de planes | Planes activos/anteriores y sus fechas, peso, ingesta y resultado. |
| `/guia` | Guía de nutrición | Macros repartidos en 3, 4 o 5 comidas, consejos y glosario. |
| `/plan/como-se-calculo` | Explicación del cálculo | Iteraciones, viabilidad, errores numéricos, gráfica y sensibilidad. |
| `/` y `*` | Redirección | Ambas llevan a `/panel`; no existe una pantalla 404 específica. |

### Componentes y estilos compartidos

| Elemento | Ubicación | Uso / oportunidad |
|---|---|---|
| Layout y navegación | [Layout.tsx](../frontend/src/components/Layout.tsx), [Layout.css](../frontend/src/styles/Layout.css) | Barra, menú de cuenta, aviso de salud, pie y modal de cierre de sesión. La navegación móvil se convierte en una fila desplazable. |
| Rutas y sesión | [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), [SesionProvider.tsx](../frontend/src/features/auth/SesionProvider.tsx) | Protección de rutas, persistencia y restauración de sesión. |
| Botones, tarjetas, KPIs y tablas | [Layout.css](../frontend/src/styles/Layout.css), [Pagina.css](../frontend/src/styles/Pagina.css) | Ya hay clases reutilizadas (`.boton`, `.tarjeta`, `.kpi`, `.tabla`); conviene consolidar su paleta y medidas sin reemplazar los elementos HTML. |
| Carga, error y vacío | Componentes de pantalla y estilos de cada feature | Panel, calendario, estadísticas, historial, guía, perfil y autenticación resuelven estos estados por separado. Un componente pequeño de estado puede unificar jerarquía, semántica y acciones de reintento. |
| Formularios | [AuthStyles.css](../frontend/src/styles/AuthStyles.css), [Perfil.css](../frontend/src/styles/Perfil.css), [NuevoPlan.css](../frontend/src/styles/NuevoPlan.css), [Calendario.css](../frontend/src/styles/Calendario.css) | Etiquetas y controles se repiten con variaciones en alturas, tamaños, bordes y foco; los validadores y los controles nativos existentes se conservan. |
| Gráficas | [ComoSeCalculo.tsx](../frontend/src/features/plan/ComoSeCalculo.tsx), [GraficaSeguimiento.tsx](../frontend/src/features/seguimiento/GraficaSeguimiento.tsx), [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx) | Recharts ya está instalado. Se pueden compartir decisiones de tipografía, colores, unidades y alternativas textuales sin forzar una gráfica genérica. |
| Diálogos | Layout y [Replaneacion.tsx](../frontend/src/features/seguimiento/Replaneacion.tsx) | Hay dos overlays con `role="dialog"`; conviene reutilizar estructura y comportamiento de teclado, manteniendo distinto su contenido y sus acciones. |
| Tablas | `Pagina.css`, [ComoSeCalculo.css](../frontend/src/styles/ComoSeCalculo.css), [Guia.css](../frontend/src/styles/Guia.css), [Estadisticas.css](../frontend/src/styles/Estadisticas.css) | Se comparten reglas parcialmente; las tablas de explicación no usan las mismas clases que las de estadísticas y guía. |
| Archivos iniciales | [App.css](../frontend/src/App.css), [index.css](../frontend/src/index.css), [main.tsx](../frontend/src/main.tsx) | `App.css` conserva estilos del starter y no se importa desde `App.tsx` ni `main.tsx`; `index.css` tiene un bloque `@theme` con nombres de color que no son variables CSS reutilizables. |

### Servicio → endpoint → pantalla

Las rutas de esta tabla se contrastaron con los routers y esquemas actuales de [auth.py](../backend/app/routes/auth.py), [usuario.py](../backend/app/routes/usuario.py), [planes.py](../backend/app/routes/planes.py), [registros.py](../backend/app/routes/registros.py), [seguimiento.py](../backend/app/routes/seguimiento.py) y [schemas](../backend/app/schemas/).

| Servicio del frontend | Endpoint real | Pantalla o consumidor |
|---|---|---|
| [authService.ts](../frontend/src/features/auth/services/authService.ts) | `POST /auth/registro` | Registro |
| [authService.ts](../frontend/src/features/auth/services/authService.ts) | `POST /auth/login` | Login |
| [authService.ts](../frontend/src/features/auth/services/authService.ts) | `GET /me` | Restauración de sesión en `SesionProvider` |
| [authService.ts](../frontend/src/features/auth/services/authService.ts) | `PATCH /me` | Perfil |
| [planService.ts](../frontend/src/features/plan/planService.ts) | `POST /plans/preview`, `POST /plans` | Nuevo plan |
| [planService.ts](../frontend/src/features/plan/planService.ts) | `GET /plans/active` | Panel y explicación del cálculo |
| [planService.ts](../frontend/src/features/plan/planService.ts) | `GET /plans/active/calculo` | Explicación del cálculo |
| [planService.ts](../frontend/src/features/plan/planService.ts) | `POST /plans/estimar-composicion` | El servicio está definido, pero ninguna pantalla lo invoca; la vista previa ya incluye composición. |
| [registroService.ts](../frontend/src/features/calendario/registroService.ts) | `GET /plans/active/calendario?mes=AAAA-MM` | Calendario |
| [registroService.ts](../frontend/src/features/calendario/registroService.ts) | `GET /actividades` | Calendario / panel de día |
| [registroService.ts](../frontend/src/features/calendario/registroService.ts) | `PUT /plans/active/calorias`, `/pesos`, `/actividades` | Panel de día del calendario |
| [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts) | `GET /plans/active/seguimiento` | Panel |
| [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts) | `POST /plans/active/replanear/preview`, `POST /plans/active/replanear` | Diálogo de re-planeación del panel |
| [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts) | `GET /plans/active/estadisticas` | Estadísticas |
| [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts) | `GET /plans` | Historial |
| [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts) | `GET /guias?comidas=3\|4\|5` | Guía |
| — | `GET /health` y `GET /` | Implementados en backend, no consumidos por el frontend; `/health` se usa como comprobación manual documentada en el README. |

**Datos disponibles que no se aprovechan o no se muestran completamente:**

- `Seguimiento` contiene `estimado`, `curva_ejercicio`, `tolerancia_kg`, la muestra `r2` y el número de pesos `n`. [GraficaSeguimiento.tsx](../frontend/src/features/seguimiento/GraficaSeguimiento.tsx) dibuja curvas, pero no diferencia visualmente los días estimados, no usa la curva de ejercicio ni presenta ajuste/tamaño de muestra; el texto de la guía sí dice que los días sin registro son estimados.
- `CalculoPlan` incluye `formulas`; la vista muestra explicaciones en lenguaje natural, pero no lee ese objeto. La sensibilidad representa mínimo y máximo, no `variantes` ni `omitidas`. [ComoSeCalculo.tsx](../frontend/src/features/plan/ComoSeCalculo.tsx), [plan.ts](../frontend/src/types/plan.ts).
- La respuesta de `/plans/active` incluye composición, método y tolerancia, además de estado y días transcurridos/restantes; el panel presenta el resumen principal, no todos esos datos. [Panel.tsx](../frontend/src/features/panel/Panel.tsx), [PlanResponse](../backend/app/schemas/plan.py).
- Estadísticas ya recibe la variación semanal y muestra los valores en tabla; solo dibuja la gráfica de adherencia, aunque el documento de software pide dos gráficas semanales. [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx), [seguimiento.py](../backend/app/schemas/seguimiento.py).
- El contrato de `POST /plans/estimar-composicion` incluye aviso, pero el servicio no está conectado a una pantalla. No se recomienda añadir una llamada redundante: `/plans/preview` ya devuelve composición.

## 3. Diagnóstico

| Área | Evidencia comprobada | Impacto para el usuario |
|---|---|---|
| Navegación móvil | [Layout.css](../frontend/src/styles/Layout.css) hace desplazable la barra por debajo de 860 px y oculta la barra de desplazamiento; los seis enlaces siguen en una sola fila. | Puede no resultar evidente que hay más destinos fuera de la pantalla; la navegación requiere desplazamiento lateral. |
| Idioma y accesibilidad | [index.html](../frontend/index.html) declara `lang="en"` aunque los textos de las pantallas están en español. Los diálogos de [Layout.tsx](../frontend/src/components/Layout.tsx) y [Replaneacion.tsx](../frontend/src/features/seguimiento/Replaneacion.tsx) tienen semántica de diálogo, pero no implementan gestión visible de foco/teclado compartida. | Lectores de pantalla pueden pronunciar español con reglas de inglés; al abrir diálogos, teclado y foco pueden dejar de seguir un recorrido claro. |
| Calendario y gráficas | [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx) oculta las marcas textuales “HOY” y “estimado” en pantallas de hasta 560 px. Las gráficas no publican un resumen textual de sus series; la cuadrícula asigna `role="grid"`/`gridcell` sin navegación de flechas. | En celular, parte de la leyenda se pierde; para teclado o lector de pantalla es más difícil interpretar y recorrer el calendario y las gráficas. |
| Retroalimentación visual | Login, registro, perfil, plan, calendario y páginas de consulta implementan mensajes y estados en elementos/clases diferentes. [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx), [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx), [Perfil.tsx](../frontend/src/features/perfil/Perfil.tsx), [NuevoPlan.tsx](../frontend/src/features/plan/NuevoPlan.tsx). | Cambian la ubicación, densidad y presentación de carga, error y ausencia de datos; no todas ofrecen reintento y el usuario no aprende un patrón consistente. |
| Solicitudes y errores | `obtenerPlanActivo` y `obtenerCalculoActivo` convierten cualquier fallo en `null` en [planService.ts](../frontend/src/features/plan/planService.ts); la carga de actividades en [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx) convierte cualquier error en catálogo vacío. | Un error de red o servidor puede parecer “sin plan”, “sin cálculo” o “sin actividades”, ocultando la causa e impidiendo al usuario recuperarse. |
| Guardado diario | [PanelDia.tsx](../frontend/src/features/calendario/PanelDia.tsx) envía en paralelo hasta tres `PUT` con `Promise.allSettled`; si uno falla, muestra error y no recarga el calendario, aunque otros pudieron guardarse correctamente. | La pantalla puede no representar lo que quedó persistido; el usuario no sabe si debe reintentar todo o solo una parte. |
| Error 403 | [clienteAxios.ts](../frontend/src/api/clienteAxios.ts) navega a `/no-autorizado`; esa ruta no existe en [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), cuyo comodín redirige al panel. | La respuesta puede terminar en un destino inesperado sin explicar la denegación. |
| Consistencia visual | [index.css](../frontend/src/index.css), [Layout.css](../frontend/src/styles/Layout.css), [AuthStyles.css](../frontend/src/styles/AuthStyles.css), [Perfil.css](../frontend/src/styles/Perfil.css), [NuevoPlan.css](../frontend/src/styles/NuevoPlan.css) y otros estilos repiten colores rojos próximos pero distintos (`#e0242b`, `#c41e24`, `#c91e27`, `#d21f28`), fondos y bordes literales. Hay radios de 8–20 px, controles de 40–46 px y tipografía de 10–14 px para elementos comparables. | Formularios y botones que deberían sentirse parte del mismo producto tienen jerarquías y dimensiones variables; parte del texto de apoyo es muy pequeño. |
| Formularios | Login, registro, perfil, plan y edición diaria vuelven a definir estilos de control; hay `aria-invalid`/`aria-describedby` en NuevoPlan, pero no se aplica el mismo patrón a todos los formularios. [AuthStyles.css](../frontend/src/styles/AuthStyles.css), [Perfil.css](../frontend/src/styles/Perfil.css), [NuevoPlan.tsx](../frontend/src/features/plan/NuevoPlan.tsx), [PanelDia.tsx](../frontend/src/features/calendario/PanelDia.tsx). | Menos consistencia entre pantallas y menor claridad sobre qué campo necesita corrección. |
| Datos y comprensión | [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx) ofrece una sola gráfica; la guía del panel afirma que los días sin registro son estimados, pero la gráfica no distingue esos tramos. [Seguimiento.ts](../frontend/src/types/seguimiento.ts), [GraficaSeguimiento.tsx](../frontend/src/features/seguimiento/GraficaSeguimiento.tsx). | El usuario puede confundir proyección con observación y tiene que inferir tendencias desde una tabla en vez de comparar el ritmo semanal visualmente. |
| Rendimiento | [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx) importa estáticamente todas las pantallas. Varias cargan Recharts, y [package.json](../frontend/package.json) ya lo incluye. No se inspeccionó ni midió el bundle durante este análisis. | El visitante de login puede descargar código de pantallas y gráficas que aún no usa; primero debe medirse y luego verificar el efecto de dividir rutas, sin inventar un tamaño inicial. |
| Mantenimiento | Las pantallas manejan solicitudes con `useEffect` y estado local; no hay script o dependencia de pruebas frontend en [package.json](../frontend/package.json). [App.css](../frontend/src/App.css) conserva estilos del starter y no está importado. | Se repiten patrones de estado y es fácil que una pantalla trate distinto el mismo error. La validación actual disponible es build/lint más revisión manual. |
| Documentación de producto | [plan-epica-planeacion.md](./plan-epica-planeacion.md) afirma que Historial no se implementa y no aparece en navegación; [Layout.tsx](../frontend/src/components/Layout.tsx), [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), [Historial.tsx](../frontend/src/features/historial/Historial.tsx) y el router de [seguimiento.py](../backend/app/routes/seguimiento.py) sí lo implementan. El documento v0.5 también enumera `/plans/active/rutina`, que no existe en los routers actuales; el backend actual soporta actividades diarias mediante `/plans/active/actividades`. | El equipo podría esperar un producto diferente al que el usuario encuentra. Se conserva el comportamiento actual; el equipo debe resolver cuál documento describe el alcance vigente. |

## 4. Decisiones de diseño y herramientas

### Adoptar

- **Mantener React + TypeScript + Vite y CSS plano.** Añadir variables CSS en `:root` y migrar selectivamente, pantalla por pantalla. No convertir hojas de estilo ni markup en una sola pasada.
- **Mantener la identidad cálida y el rojo actuales**, con un único valor canónico para cada función. Valores iniciales propuestos:

| Variable | Valor propuesto | Uso |
|---|---|---|
| `--color-fondo` | `#f7f5f2` | Fondo general |
| `--color-superficie` | `#ffffff` | Tarjetas y formularios |
| `--color-texto` | `#171719` | Texto principal |
| `--color-texto-secundario` | `#5d5960` | Texto explicativo |
| `--color-texto-sutil` | `#68636a` | Ayuda; validar contraste antes de usar en texto pequeño |
| `--color-borde` | `#e6e1db` | Bordes y separadores |
| `--color-primario` | `#c41e24` | Acción/enlace principal |
| `--color-primario-hover` | `#ad1820` | Interacción hover |
| `--color-exito` / `--color-fondo-exito` | `#1c6b3a` / `#f1faf4` | Confirmaciones |
| `--color-aviso` / `--color-fondo-aviso` | `#755600` / `#fffaf0` | Advertencias; ajustar contra contraste medido |
| `--color-error` / `--color-fondo-error` | `#a3161d` / `#fdf1f1` | Errores |
| `--anillo-foco` | `#7f171c` | Indicador visible de foco |
| `--fuente-interfaz` | `Arial, Helvetica, sans-serif` | Conserva la fuente del producto actual |
| `--texto-base` | `16px` | Texto normal; ajustar el mínimo de ayudas en la revisión visual |
| `--espacio-1…6` | `4px, 8px, 12px, 16px, 24px, 32px` | Ritmo de espacios |
| `--radio-control`, `--radio-tarjeta`, `--radio-grande` | `8px, 12px, 16px` | Controles, tarjetas y contenedores |

- **Reutilizar HTML nativo** (`button`, `label`, `input`, `select`, tabla, enlaces) y las clases compartidas `.boton`, `.tarjeta`, `.kpi` y `.tabla`; incorporar componentes React solo para patrones repetidos con comportamiento/semántica propia, como estados de solicitud y diálogos.
- **Usar `React.lazy` y `Suspense`** (ya incluidos en React) para cargar pantallas por ruta. Medir `npm run build` antes/después y confirmar que las rutas de gráficas no se descargan al entrar en login.
- **Mantener Recharts** para las gráficas actuales; añadir alternativas textuales y presentar datos suficientes para que la tendencia no dependa solo del color o de la interacción con la gráfica.
- **Mantener el estado remoto local y explícito al inicio.** No añadir una caché global hasta que un caso de actualización entre pantallas la justifique. La interfaz debe mostrar errores reales, volver a consultar después de guardar y no convertir una falla en “vacío”.
- **No alterar endpoints, modelos ni cálculos.** Los tipos del frontend se contrastan con los esquemas Pydantic existentes; las mejoras visuales consumen los datos que ya devuelve la API.

### Descartar

- No incorporar Tailwind, CSS-in-JS, una librería de componentes, iconos ni una biblioteca de consultas remotas en esta entrega. No hay un problema observado que justifique migración, dependencia y cambio de estilo; CSS, React, React Router y Recharts ya cubren el alcance.
- No sustituir Recharts ni duplicar en el cliente los cálculos del backend.
- No instalar dependencias nuevas. Por tanto, no hay peso añadido que justificar; si una tarea futura necesitara una dependencia, debe incluir peso medido, problema concreto y alternativa sin dependencia antes de solicitar aprobación.

## 5. Flujo de trabajo fijo

Repetir estos pasos para **cada tarea**, siempre en este orden:

1. Leer los archivos listados en la tarea y su referencia funcional/API; confirmar qué comportamiento y ruta deben preservarse.
2. Buscar componentes, estilos, servicios y patrones existentes que se puedan reutilizar; no añadir otro patrón sin explicar por qué.
3. Presentar el cambio delimitado, sus archivos y criterios de aceptación; **esperar aprobación antes de modificar**.
4. Implementar únicamente el alcance aprobado, en un commit pequeño, sin cambiar backend ni contratos.
5. Verificar con `npm run build` y `npm run lint`; luego revisar en pantalla el flujo afectado, teclado y vista móvil indicados en los criterios.
6. Informar el resultado, cualquier limitación y un mensaje de commit sugerido; no afirmar verificaciones que no se hayan ejecutado.

El agente puede ejecutar en `frontend/` `npm run build` y `npm run lint`, así como iniciar el servidor de desarrollo cuando tenga acceso al entorno visual. El usuario ejecuta la revisión visual o comparte evidencia si el agente no tiene ese acceso. No se añade ni instala tooling de pruebas. Los cambios aprobados a una tarea se entregan en un commit independiente.

## 6. Fases y tareas

### Fase 1 · Cimientos compartidos

#### F1-01 · Definir variables de diseño y el idioma del documento

- **Objetivo:** que todas las pantallas partan de una paleta, tipografía y ritmo visual reconocibles, y que lectores de pantalla interpreten el contenido como español.
- **Leer:** [index.css](../frontend/src/index.css), [index.html](../frontend/index.html), [Layout.css](../frontend/src/styles/Layout.css), [README.md](../README.md).
- **Modificar:** `frontend/src/index.css`, `frontend/index.html`.
- **Reutilizar:** colores, fuente y medidas ya presentes en `Layout.css`/`Pagina.css`; conservar el contenido y estructura de la app.
- **Cambios concretos:** declarar los tokens de la sección 4 en `:root`; normalizar tipografía base, foco visible y movimiento reducido sin rediseñar pantallas; cambiar `lang` a `es`. No migrar todavía todos los literales.
- **Aceptación:** `document.documentElement.lang === "es"`; tokens disponibles en la cascada global; links, botones y controles conservan un foco claramente visible; se mantiene el renderizado de rutas.
- **Verificar:** build/lint del flujo fijo; abrir una pantalla de texto, formulario y gráfica, comprobar foco por teclado y verificar que el movimiento reducido no anima la entrada de resultados.
- **Dependencias:** ninguna.
- **Commit sugerido:** `style(frontend): definir tokens visuales y declarar idioma español`

#### F1-02 · Crear estados compartidos para solicitudes

- **Objetivo:** que las esperas, fallos y estados vacíos se entiendan igual y ofrezcan una acción apropiada.
- **Leer:** [Pagina.css](../frontend/src/styles/Pagina.css), [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx), [Panel.tsx](../frontend/src/features/panel/Panel.tsx), [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx).
- **Crear:** `frontend/src/components/EstadoPantalla.tsx`, `frontend/src/styles/EstadoPantalla.css`.
- **Reutilizar:** mensajes actuales en español, `.pagina__estado`, `.pagina__error`, `.tarjeta--vacia` y los tokens F1-01.
- **Cambios concretos:** componente pequeño con variantes explícitas de carga, error y vacío; acepta contenido y acción de reintento/enlace, sin solicitar datos ni ocultar errores. Semántica accesible adecuada (`role="status"`/`role="alert"` según el caso).
- **Aceptación:** cada variante tiene nombre/texto comprensible; acción opcional es operable por teclado; la variante vacía no se usa para representar errores; no introduce dependencia.
- **Verificar:** build/lint del flujo fijo; renderizar las tres variantes con lector de pantalla/inspector de accesibilidad y comprobar foco de la acción.
- **Dependencias:** F1-01.
- **Commit sugerido:** `feat(frontend): añadir estados compartidos de pantalla`

#### F1-03 · Hacer reconocible y operable la navegación móvil

- **Objetivo:** que la persona encuentre las secciones sin perder la ruta activa ni depender de un gesto oculto.
- **Leer:** [Layout.tsx](../frontend/src/components/Layout.tsx), [Layout.css](../frontend/src/styles/Layout.css), [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx).
- **Modificar:** `frontend/src/components/Layout.tsx`, `frontend/src/styles/Layout.css`.
- **Reutilizar:** `NavLink`, nombres en español y las seis rutas actuales del menú.
- **Cambios concretos:** mantener el patrón de navegación existente y sus destinos; mejorar señales de desbordamiento/scroll móvil, estado activo y foco visible; garantizar que el menú de cuenta no tape ni desplace los enlaces.
- **Aceptación:** las seis rutas continúan visibles/alcanzables en escritorio y móvil; se puede recorrer con Tab y activar con Enter; la ruta activa se distingue sin depender solo del color; no se añade una ruta ni un patrón nuevo de menú.
- **Verificar:** build/lint del flujo fijo; probar `/panel`, `/calendario` y `/nuevo-plan` a 375 px y 1280 px, recorrer enlaces con teclado.
- **Dependencias:** F1-01.
- **Commit sugerido:** `style(frontend): mejorar navegación responsive y foco activo`

#### F1-04 · Compartir el comportamiento accesible de los diálogos

- **Objetivo:** que confirmar cierre de sesión o re-planeación no saque al usuario del recorrido de teclado.
- **Leer:** [Layout.tsx](../frontend/src/components/Layout.tsx), [Layout.css](../frontend/src/styles/Layout.css), [Replaneacion.tsx](../frontend/src/features/seguimiento/Replaneacion.tsx), [Panel.css](../frontend/src/styles/Panel.css).
- **Crear/modificar:** crear `frontend/src/components/Dialogo.tsx`; modificar `frontend/src/components/Layout.tsx`, `frontend/src/features/seguimiento/Replaneacion.tsx` y los estilos existentes de diálogo en `Layout.css`/`Panel.css`.
- **Reutilizar:** overlay, clases `.modal`, títulos/etiquetas, acciones y contenido actuales.
- **Cambios concretos:** extraer la estructura común; al abrir, enfocar el diálogo/acción inicial; cerrar con Escape, mantener el foco dentro mientras esté abierto y devolverlo al control que lo abrió; conservar cierre al cancelar y las acciones existentes.
- **Aceptación:** ambos diálogos identifican título y modalidad; teclado no llega a controles de fondo; Escape/cancelar restaura foco; cerrar sesión y confirmar re-planeación conservan su resultado actual.
- **Verificar:** build/lint del flujo fijo; probar ambos diálogos con Tab, Shift+Tab, Escape, clic exterior y tecnologías de asistencia disponibles.
- **Dependencias:** F1-01.
- **Commit sugerido:** `feat(frontend): unificar diálogos accesibles`

### Fase 2 · Solicitudes, errores y guardado

#### F2-01 · Diferenciar “sin plan” de un fallo al consultar el plan

- **Objetivo:** que una caída del servidor no se presente como si no existiera un plan.
- **Leer:** [planService.ts](../frontend/src/features/plan/planService.ts), [PantallaCalculo.tsx](../frontend/src/features/plan/PantallaCalculo.tsx), [plan.py](../backend/app/routes/planes.py), [plan.py](../backend/app/schemas/plan.py).
- **Modificar:** `frontend/src/features/plan/planService.ts`, `frontend/src/features/plan/PantallaCalculo.tsx`.
- **Reutilizar:** `esSinPlan`, `mensajeDeError` y F1-02.
- **Cambios concretos:** mapear solo el 404 esperado de ausencia de plan/cálculo a estado vacío; propagar otros errores; representar carga, error con reintento y ausencia con mensajes distintos. No envolver errores de `Promise.all` en una salida “sin plan”.
- **Aceptación:** un 404 mantiene el mensaje/enlace de crear plan; un 500 o error de red muestra error recuperable; éxito muestra plan y cálculo; las llamadas y respuestas siguen siendo las mismas.
- **Verificar:** build/lint del flujo fijo; simular éxito, 404, 500 y desconexión al abrir `/plan/como-se-calculo`.
- **Dependencias:** F1-02.
- **Commit sugerido:** `fix(frontend): distinguir errores de ausencia de plan`

#### F2-02 · Informar fallos al cargar el catálogo de actividades

- **Objetivo:** que el usuario sepa por qué no puede elegir una actividad y pueda volver a intentarlo.
- **Leer:** [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx), [PanelDia.tsx](../frontend/src/features/calendario/PanelDia.tsx), [registroService.ts](../frontend/src/features/calendario/registroService.ts), [registro.py](../backend/app/routes/registros.py).
- **Modificar:** `frontend/src/features/calendario/Calendario.tsx`.
- **Reutilizar:** servicio `obtenerCatalogoActividades`, el control deshabilitado y F1-02.
- **Cambios concretos:** modelar carga/error/éxito del catálogo; eliminar la conversión silenciosa de error a lista vacía; mostrar reintento sin bloquear la lectura del calendario si este sí cargó.
- **Aceptación:** catálogo vacío real y error de carga no se confunden; reintentar actualiza el selector; calendario, calorías y peso siguen disponibles aunque el catálogo falle.
- **Verificar:** build/lint del flujo fijo; simular `/actividades` con éxito, lista vacía y error, y revisar el panel de día.
- **Dependencias:** F1-02.
- **Commit sugerido:** `fix(calendario): mostrar y recuperar errores del catálogo`

#### F2-03 · Alinear la vista con los guardados parciales de un día

- **Objetivo:** que, si una de varias modificaciones no se guarda, el calendario muestre qué persistió y qué debe corregirse.
- **Leer:** [PanelDia.tsx](../frontend/src/features/calendario/PanelDia.tsx), [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx), [registroService.ts](../frontend/src/features/calendario/registroService.ts), [registro.py](../backend/app/routes/registros.py), [registro.py](../backend/app/schemas/registro.py).
- **Modificar:** `frontend/src/features/calendario/PanelDia.tsx`, `frontend/src/features/calendario/Calendario.tsx`.
- **Reutilizar:** `Promise.allSettled`, las tres llamadas `PUT` actuales, `mensajeDeError` y el refresco del mes por versión.
- **Cambios concretos:** conservar cada resultado de la operación; ante éxito parcial, volver a consultar el calendario y mostrar resultado parcial explícito sin presentar el conjunto como guardado; no inventar transacciones ni cambiar el contrato.
- **Aceptación:** fallo total, éxito total y éxito parcial tienen mensajes distintos; tras un éxito parcial los valores visibles coinciden con la siguiente lectura del backend; el botón evita envíos duplicados mientras guarda.
- **Verificar:** build/lint del flujo fijo; simular fallo de cada `PUT` por separado y comprobar el contenido persistido/mostrado.
- **Dependencias:** F1-02.
- **Commit sugerido:** `fix(calendario): reflejar resultados parciales al guardar`

#### F2-04 · Mantener los errores 403 en el contexto de la pantalla

- **Objetivo:** que una denegación o una falla al validar sesión tenga explicación sin borrar credenciales ni enviar al usuario a una ruta inexistente.
- **Leer:** [clienteAxios.ts](../frontend/src/api/clienteAxios.ts), [SesionProvider.tsx](../frontend/src/features/auth/SesionProvider.tsx), [authService.ts](../frontend/src/features/auth/services/authService.ts), [mensajeError.ts](../frontend/src/api/mensajeError.ts), [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), routers backend.
- **Modificar:** `frontend/src/api/clienteAxios.ts`, `frontend/src/features/auth/SesionProvider.tsx`.
- **Reutilizar:** evento `EVENTO_SESION_EXPIRADA`, `avisoSesion`, estado de navegación al login y mensajes de error actuales; no confundir 403/errores transitorios con 401/sesión expirada.
- **Cambios concretos:** quitar la navegación forzada a `/no-autorizado`; en la restauración de sesión, reservar limpieza de credenciales para 401 y dejar una explicación/reintento visible si la validación falla por otra respuesta. No agregar ruta ni cambiar backend.
- **Aceptación:** 403 no navega a una ruta inexistente ni se presenta como sesión expirada; un error transitorio al consultar `/me` no elimina el token y deja un mensaje en español; 401 sigue limpiando sesión y mostrando el aviso de expiración.
- **Verificar:** build/lint del flujo fijo; simular 403, 401 y desconexión durante una solicitud normal y durante restauración de sesión.
- **Dependencias:** F1-02.
- **Commit sugerido:** `fix(api): evitar redirección a ruta de acceso inexistente`

### Fase 3 · Aplicación incremental a las pantallas

#### F3-01 · Aclarar validación y envío en acceso y registro

- **Objetivo:** que el visitante complete su cuenta con menos dudas y entienda qué necesita corregir.
- **Leer:** [Login.tsx](../frontend/src/features/auth/Login.tsx), [Registro.tsx](../frontend/src/features/auth/Registro.tsx), [AuthStyles.css](../frontend/src/styles/AuthStyles.css), [auth.py](../backend/app/schemas/auth.py).
- **Modificar:** `frontend/src/features/auth/Login.tsx`, `frontend/src/features/auth/Registro.tsx`, `frontend/src/styles/AuthStyles.css`.
- **Reutilizar:** formulario en dos pasos, requisitos de contraseña en vivo, `mensajeDeError`, `role="alert"` y tokens.
- **Cambios concretos:** vincular mensajes de campo con sus controles (`aria-describedby`/`aria-invalid` cuando aplique), mantener el foco al avanzar o fallar, comunicar envío en curso y mejorar tamaño/foco de botones y texto de ayuda. Conservar validaciones, español y destinos.
- **Aceptación:** cada error puede asociarse a un campo y se anuncia; los requisitos existentes de contraseña siguen visibles; los botones bloquean doble envío y muestran progreso; se conserva el retorno tras login.
- **Verificar:** build/lint del flujo fijo; completar login exitoso/fallido, ambos pasos de registro y comprobación con teclado a 375 px y escritorio.
- **Dependencias:** F1-01, F1-02.
- **Commit sugerido:** `feat(auth): mejorar accesibilidad y feedback de formularios`

#### F3-02 · Hacer más claro el guardado del perfil

- **Objetivo:** que la persona detecte campos inválidos y confirme si los cambios se guardaron.
- **Leer:** [Perfil.tsx](../frontend/src/features/perfil/Perfil.tsx), [Perfil.css](../frontend/src/styles/Perfil.css), [perfil.py](../backend/app/schemas/perfil.py), [auth.py](../backend/app/schemas/auth.py).
- **Modificar:** `frontend/src/features/perfil/Perfil.tsx`, `frontend/src/styles/Perfil.css`.
- **Reutilizar:** PATCH actual, comparación de cambios, mensajes de error/éxito y tokens.
- **Cambios concretos:** asociar mensajes de validación a campos y marcar validez; armonizar alturas, foco, tamaño de texto y acciones con el sistema; preservar el correo de solo lectura y la nota de que los cambios aplican a planes futuros.
- **Aceptación:** el error indica campo/acción; el éxito solo aparece después de respuesta del servidor; descartar restaura datos vigentes; cambios vacíos no envían PATCH.
- **Verificar:** build/lint del flujo fijo; probar guardar, descartar, errores de validación y respuesta API, con teclado y móvil.
- **Dependencias:** F1-01, F1-02.
- **Commit sugerido:** `style(perfil): unificar validación y confirmación de cambios`

#### F3-03 · Explicar la vista previa del plan con jerarquía y evidencia

- **Objetivo:** que el usuario pueda comparar viabilidad, resultado e incertidumbre antes de confirmar.
- **Leer:** [NuevoPlan.tsx](../frontend/src/features/plan/NuevoPlan.tsx), [ComoSeCalculo.tsx](../frontend/src/features/plan/ComoSeCalculo.tsx), [NuevoPlan.css](../frontend/src/styles/NuevoPlan.css), [ComoSeCalculo.css](../frontend/src/styles/ComoSeCalculo.css), [plan.ts](../frontend/src/types/plan.ts), [plan.py](../backend/app/schemas/plan.py).
- **Modificar:** `frontend/src/features/plan/NuevoPlan.tsx`, `frontend/src/features/plan/ComoSeCalculo.tsx`, `frontend/src/styles/NuevoPlan.css`, `frontend/src/styles/ComoSeCalculo.css`.
- **Reutilizar:** campos y validadores existentes, `VistaPreviaPlan`, bloqueos/avisos, tabla Secante y gráfica de tolerancia actual.
- **Cambios concretos:** organizar resultado en resumen prioritario, advertencias/bloqueos, detalles y acción de confirmar; presentar sensibilidad y método de composición con su advertencia; mostrar fórmulas disponibles si mejoran comprensión; ofrecer título/resumen textual y alternativas a la gráfica; asegurar que la curva y banda de tolerancia no desaparezcan del resultado visual.
- **Aceptación:** ningún bloqueo permite confirmar; la fecha viable, la ingesta y los macros se distinguen claramente; resultado y explicación muestran las cifras entregadas, sin cálculos nuevos; la gráfica tiene descripción/unidades y se lee en móvil.
- **Verificar:** build/lint del flujo fijo; revisar flujo viable, no viable, advertencias y campos incompletos a 375 px y 1280 px; comprobar que editar datos invalida la vista previa.
- **Dependencias:** F1-01, F1-02.
- **Commit sugerido:** `feat(plan): priorizar viabilidad e incertidumbre en la vista previa`

#### F3-04 · Hacer interpretable el seguimiento del panel

- **Objetivo:** distinguir lo medido de lo estimado y entender cómo el progreso se compara con el plan.
- **Leer:** [Panel.tsx](../frontend/src/features/panel/Panel.tsx), [GraficaSeguimiento.tsx](../frontend/src/features/seguimiento/GraficaSeguimiento.tsx), [Panel.css](../frontend/src/styles/Panel.css), [seguimiento.ts](../frontend/src/types/seguimiento.ts), [seguimiento.py](../backend/app/schemas/seguimiento.py).
- **Modificar:** `frontend/src/features/panel/Panel.tsx`, `frontend/src/features/seguimiento/GraficaSeguimiento.tsx`, `frontend/src/styles/Panel.css`.
- **Reutilizar:** series, leyenda, curva meta, helper de formato y botón de registrar hoy actuales.
- **Cambios concretos:** etiquetar datos reales, proyección y tramos estimados usando `estimado`; exponer una breve explicación/resumen junto a la gráfica; mostrar R² y cantidad de pesos cuando haya tendencia; ordenar métricas por acción siguiente y meta.
- **Aceptación:** las series se distinguen por nombre y estilo además de color; se identifica cuándo faltan registros; R²/n no se presentan si no hay tendencia; la acción principal sigue llevando a `/calendario`.
- **Verificar:** build/lint del flujo fijo; revisar panel con pocos/suficientes pesos, con y sin sugerencia de re-planeación, y con días estimados.
- **Dependencias:** F1-01, F1-02, F2-01.
- **Commit sugerido:** `feat(panel): distinguir registros y proyecciones`

#### F3-05 · Mejorar el calendario en celular y con teclado

- **Objetivo:** que se pueda ubicar y editar cada día sin perder información en pantallas pequeñas.
- **Leer:** [Calendario.tsx](../frontend/src/features/calendario/Calendario.tsx), [PanelDia.tsx](../frontend/src/features/calendario/PanelDia.tsx), [Calendario.css](../frontend/src/styles/Calendario.css), [registro.ts](../frontend/src/types/registro.ts).
- **Modificar:** `frontend/src/features/calendario/Calendario.tsx`, `frontend/src/features/calendario/PanelDia.tsx`, `frontend/src/styles/Calendario.css`.
- **Reutilizar:** navegación mensual, leyenda, selector de día y formulario del panel.
- **Cambios concretos:** mantener fechas y leyenda legibles en móvil (sin ocultar la única etiqueta “hoy/estimado”); mejorar hit targets/foco y navegación por teclado de la cuadrícula; clarificar seleccionado, fuera de plan, futuro, registrado y estimado con texto y forma/patrón además de color.
- **Aceptación:** todos los días habilitados son alcanzables por teclado y la selección se anuncia; leyenda y estado no dependen solo de color; panel del día y controles no generan scroll horizontal a 375 px.
- **Verificar:** build/lint del flujo fijo; probar meses anterior/siguiente y un día registrado/estimado/futuro, selección/guardado con teclado en móvil y escritorio.
- **Dependencias:** F1-01, F1-02, F2-02, F2-03.
- **Commit sugerido:** `feat(calendario): mejorar lectura móvil y navegación por teclado`

#### F3-06 · Completar la lectura visual de estadísticas semanales

- **Objetivo:** comparar el ritmo de peso y la adherencia sin depender de recorrer siete columnas de una tabla.
- **Leer:** [Estadisticas.tsx](../frontend/src/features/estadisticas/Estadisticas.tsx), [Estadisticas.css](../frontend/src/styles/Estadisticas.css), [seguimiento.ts](../frontend/src/types/seguimiento.ts), [seguimiento.py](../backend/app/schemas/seguimiento.py).
- **Modificar:** `frontend/src/features/estadisticas/Estadisticas.tsx`, `frontend/src/styles/Estadisticas.css`.
- **Reutilizar:** datos de `semanas`, formato numérico, tabla actual y Recharts instalado.
- **Cambios concretos:** añadir una gráfica pequeña de variación/peso semanal a partir de los datos recibidos; conservar la tabla como detalle y alternativa textual; clarificar semana parcial y denominador de adherencia.
- **Aceptación:** gráfica usa exclusivamente respuesta API; semana sin observación no se dibuja como cero real; cada gráfica tiene título, unidades y resumen; tabla sigue disponible y se puede recorrer en móvil.
- **Verificar:** build/lint del flujo fijo; revisar cero registros, semanas parciales y completas, pesos ausentes, y tabla en viewport estrecho.
- **Dependencias:** F1-01, F1-02.
- **Commit sugerido:** `feat(estadisticas): visualizar también el cambio semanal de peso`

#### F3-07 · Dar respuesta inmediata al cambiar la guía

- **Objetivo:** saber qué reparto está viendo y si se está recalculando al elegir el número de comidas.
- **Leer:** [Guia.tsx](../frontend/src/features/guia/Guia.tsx), [Guia.css](../frontend/src/styles/Guia.css), [seguimientoService.ts](../frontend/src/features/seguimiento/seguimientoService.ts), [seguimiento.py](../backend/app/schemas/seguimiento.py).
- **Modificar:** `frontend/src/features/guia/Guia.tsx`, `frontend/src/styles/Guia.css`.
- **Reutilizar:** opciones 3/4/5, `GET /guias`, tabla, consejos y glosario.
- **Cambios concretos:** distinguir la respuesta correspondiente a la selección actual de la anterior mientras carga; anunciar actualización/error; mejorar foco/selección del control y desplazamiento horizontal de la tabla en móvil.
- **Aceptación:** no se presenta el reparto anterior como si fuera el nuevo; selector es operable y anunciado; fallos no borran silenciosamente la guía; textos en español y valores vienen de API.
- **Verificar:** build/lint del flujo fijo; cambiar rápidamente 3/4/5 comidas y simular respuesta lenta/error, verificar móvil.
- **Dependencias:** F1-01, F1-02.
- **Commit sugerido:** `feat(guia): mejorar respuesta del selector de comidas`

#### F3-08 · Alinear presentación del historial sin cambiar su disponibilidad

- **Objetivo:** entender cuál plan está vigente y cómo se relacionan los anteriores.
- **Leer:** [Historial.tsx](../frontend/src/features/historial/Historial.tsx), [Historial.css](../frontend/src/styles/Historial.css), [Layout.tsx](../frontend/src/components/Layout.tsx), [seguimiento.py](../backend/app/routes/seguimiento.py), [plan-epica-planeacion.md](./plan-epica-planeacion.md).
- **Modificar:** `frontend/src/features/historial/Historial.tsx`, `frontend/src/styles/Historial.css`.
- **Reutilizar:** `GET /plans`, tarjetas, etiquetas activo/anterior, fechas y enlaces actuales.
- **Cambios concretos:** jerarquizar estado activo, fechas y resultado; dar estados de carga/error/vacío consistentes y hacer el resumen legible en móvil. Mantener `/historial`, enlace de navegación y datos actuales hasta una decisión expresa del equipo.
- **Aceptación:** activo y anteriores se distinguen sin depender solo del color; errores no se muestran como lista vacía; la lista y enlaces conservan comportamiento actual y no hay overflow a 375 px.
- **Verificar:** build/lint del flujo fijo; revisar cero, uno y varios planes, estado activo y anterior en móvil.
- **Dependencias:** F1-01, F1-02. Si el equipo decide retirar Historial, esta tarea se pausa y se solicita aprobación específica antes de cualquier cambio de ruta.
- **Commit sugerido:** `style(historial): clarificar plan activo y planes anteriores`

### Fase 4 · Carga inicial

#### F4-01 · Diferir las pantallas y gráficas por ruta

- **Objetivo:** que el visitante reciba primero lo necesario para la pantalla que abrió, sin descargar de entrada todo el seguimiento.
- **Leer:** [RutasApp.tsx](../frontend/src/routes/RutasApp.tsx), [App.tsx](../frontend/src/App.tsx), [package.json](../frontend/package.json), [vite.config.ts](../frontend/vite.config.ts).
- **Modificar:** `frontend/src/routes/RutasApp.tsx` y, solo si hace falta, el estado reutilizable creado en F1-02.
- **Reutilizar:** React, React Router y Vite ya instalados; mantener los mismos elementos, protecciones y destinos de ruta.
- **Cambios concretos:** cargar vistas con `React.lazy`/`Suspense` y estado de carga accesible; mantener lazy las pantallas que usan Recharts; no instalar analizadores ni modificar la API.
- **Aceptación:** todas las URLs/direct links, rutas públicas/privadas y redirecciones conservan comportamiento; `/login` no solicita los módulos de las pantallas/gráficas que no abre; registrar y comparar el tamaño de chunks del build previo y posterior, sin fijar un umbral hasta conocer la línea base.
- **Verificar:** build/lint del flujo fijo; comparar la salida de Vite antes/después y revisar solicitudes al abrir login, panel y estadísticas; probar URL directa de cada ruta.
- **Dependencias:** F1-02 y las tareas de pantalla que se hayan aprobado; medir la línea base antes de este commit.
- **Commit sugerido:** `perf(frontend): diferir pantallas y gráficas por ruta`

## 7. Acciones que debe hacer el usuario

- **Antes de la primera revisión visual:** si las dependencias del frontend no están instaladas, desde `frontend/` ejecutar `npm install`; iniciar el backend según [README.md](../README.md) y ejecutar `npm run dev` en otra terminal para probar la aplicación completa.
- **En cada tarea aprobada:** aprobar o pedir ajustes a la propuesta antes de implementar. El agente puede correr `npm run build` y `npm run lint`; el usuario ejecuta `npm run dev` y comprueba pantallas solo si el agente no dispone de navegador/entorno visual, o aporta captura/reproducción.
- **Dependencias nuevas:** ninguna prevista, no ejecutar una instalación adicional ni modificar `package.json`/lockfile por este plan.
- **Antes de F3-08:** confirmar si el alcance vigente permite conservar y pulir Historial, dado que la documentación y el código se contradicen. Mientras no haya decisión, se conservan ruta y comportamiento actuales.
- **Antes de F4-01:** aprobar la línea base de tamaño obtenida por `npm run build`; no se prescribe un presupuesto numérico sin medirla primero.

## 8. Fuera de alcance y preguntas abiertas

### Fuera de alcance

- Cambios en FastAPI, esquemas, persistencia, cálculos, seguridad de la cuenta y contratos de endpoints.
- Nuevas funciones (alimentos, recuperación de contraseña, autenticación social, app nativa), nuevos endpoints y sustitución de servicios existentes.
- Migrar CSS a otra metodología, rediseño de marca, reemplazo de Recharts o instalación de una librería de componentes/estado remoto.
- Retirar o renombrar rutas, cambiar textos al inglés o alterar los flujos funcionales actuales.
- Ejecutar build, lint, instalaciones u otros comandos durante la elaboración de este plan.

### Preguntas para el equipo

1. ¿La implementación actual de Historial (`/historial`, enlace y `GET /plans`) es el alcance vigente, o sigue vigente la decisión de retirarlo descrita en `plan-epica-planeacion.md`? La restricción de este plan es preservar la ruta hasta recibir decisión.
2. El documento v0.5 describe rutina semanal y menciona `/plans/active/rutina`, mientras que el backend/frontend actual ofrecen actividades diarias y `/plans/active/actividades`. ¿Se confirma como fuente funcional vigente el comportamiento implementado y documentado en el README?
3. ¿Hay un estándar de contraste/tamaño mínimo de texto ya adoptado por el equipo? Si no lo hay, validar los tokens propuestos y priorizar contraste WCAG AA para texto normal y controles antes de cerrar F1-01.

