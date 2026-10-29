# MacroSolver · motor numérico (v0.1.0)

Paquete de Python puro, sin dependencias, que implementa la sección 5 del
*Documento de software v0.5*. No conoce la base de datos ni la red: el backend
(FastAPI) arma los datos, convierte fechas a índices y llama a estas funciones.

## Probar

Desde `backend/`, con el entorno virtual del backend activo:

```bash
pip install pytest
pytest -v                # 50 pruebas: V1–V8 (V5 son las 6 pruebas de la beta) y reglas
python demo_motor.py     # plan de ejemplo, seguimiento, re-planeación y tabla de V1
```

El motor no necesita `.env` ni Supabase: las pruebas no importan `app/`.

## Estructura

| Módulo | Sección | Contenido |
| --- | --- | --- |
| `constantes.py` | 5.1 | ρF, ρL, c_F, bloqueos, tolerancias, MET |
| `tipos.py` | — | `Perfil`, `Trayectoria`, `ErrorMotor` (el backend lo responde como 422) |
| `energia.py` | 5.2 | `tmb`, `tdee`, `equilibrio` (W*) |
| `composicion.py` | 5.3 | `estimar_grasa` (Marina con respaldo Deurenberg) |
| `modelo.py` | 5.4, 5.5, 5.12 | `simular_composicion` (Euler), `referencia_rk4`, `euler_simple`, soluciones exactas |
| `viabilidad.py` | 5.6 | `ingesta_rapida`, `evaluar_viabilidad`, `cumple_bloqueos` |
| `secante.py` | 5.7 | `secante_salvaguardada`, `calcular_ingesta_meta`, `biseccion` (solo para V2) |
| `macros.py` | 5.8 | `macros` con respaldo de grasa al 20 % |
| `seguimiento.py` | 5.9 | `simular_adherencia`, `llegada_estimada`, `regresion_exponencial`, `evaluar_replaneacion`, `composicion_replaneacion` |
| `estadisticas.py` | 5.10 | `estadisticas_semanales` (domingo a sábado) |
| `sensibilidad.py` | 5.11 | `derivada_central`, `rango_ingesta` |
| `ciclo.py` | 10 | `calcular_vista_previa` (/plans/preview) y `calcular_seguimiento` (/seguimiento) |
| `beta.py` | — | API de la beta (commit f1088b4) para que sus 6 pruebas sigan en verde (V5); el sistema nuevo no la usa |

## Convención de índices

El día `i` es `fecha_inicio + i`. La ingesta del día `i` lleva de `W_i` a `W_(i+1)`.
Los registros entran como diccionarios `{día: valor}`; los pesos deben incluir el día 0.

## Uso desde el backend

```python
from macrosolver import Perfil, calcular_vista_previa, calcular_seguimiento, ErrorMotor

perfil = Perfil(sexo="hombre", edad=23, altura_cm=176, f_act=1.375)
try:
    vp = calcular_vista_previa(perfil, W0=82, W_meta=75, N=90, cuello=39, cintura=101)
except ErrorMotor as e:
    ...  # HTTPException(422, {"codigo": e.codigo, "mensaje": e.mensaje})

if vp.viabilidad.viable:
    vp.ingesta, vp.macros, vp.curva_ideal["W"], vp.historial_secante, vp.rango
else:
    vp.viabilidad.n_min_dias   # fecha viable = fecha_inicio + n_min_dias
```

## Pendientes conocidos

- **Edad:** el motor acepta de 18 a 100 años (README del repo); el script SQL y los mockups aún dicen 14.
- **Re-planeación inviable:** si el plazo restante es menor que el mínimo seguro, el documento no dice qué hacer.
  La demo propone el plazo mínimo; falta decidirlo y reflejarlo en HU-14.
- Citar las fuentes marcadas en el documento (Marina, Deurenberg, Hall 2008, tope de 700 kcal, 2,2 g/kg, MET).
