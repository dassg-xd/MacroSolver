# MacroSolver (beta, sin base de datos)

Prueba de la logica principal con datos de prueba: **Euler + Secante + Minimos Cuadrados + Re-planeacion**.
No se conecta a Supabase ni necesita datos reales.

## Estructura

```
MacroSolver/
├── app.py                    Interfaz web de prueba (Streamlit)
├── ejecutar_demo.py          Demo sin interfaz: imprime resumen y guarda graficas en salida/
├── requirements.txt          Librerias necesarias
├── macrosolver/              Logica del proyecto
│   ├── modelo.py             TMB, TDEE y macronutrientes
│   ├── metodos_numericos.py  Euler, Secante y regresion por minimos cuadrados
│   ├── ciclo.py              Planeacion -> adherencia -> tendencia -> re-planeacion
│   ├── datos_prueba.py       Generador de usuarios simulados y lectura de datos manuales
│   └── graficas.py           Graficas (matplotlib)
├── tests/
│   └── test_logica.py        Verificaciones automaticas
├── bd/
│   └── macrosolver.sql       Script para crear las tablas en Supabase (aun no se usa)
├── docs/
│   ├── documentacion_proyecto.md   Documentacion original del proyecto
│   └── macrosolver_bd.drawio       Diagrama de la base de datos
└── salida/                   Aqui se guardan las graficas del demo
```

## Datos de prueba

En la interfaz, el generador crea un usuario simulado (cuanto se desvia del plan, variabilidad diaria
y ruido de la bascula). Los datos aparecen en dos cuadros de texto que puedes editar a mano con el
formato `dia, valor`, una linea por registro:

```
Calorias reales            Pesos reales (dia 0 = inicial)
1, 2150                    0, 90.00
2, 1980                    7, 89.30
...                        14, 88.70
```
