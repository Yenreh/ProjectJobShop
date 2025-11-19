# Job Shop Scheduling Solver

Herramienta interactiva para resolver problemas de Job Shop Scheduling Problem (JSSP) utilizando Programación por Restricciones con MiniZinc.

## Descripción

Esta aplicación web permite ejecutar modelos de Programación por Restricciones para resolver instancias del Job Shop Scheduling Problem con diferentes variaciones:

- **Job Shop con Operarios Limitados**: Modela el problema cuando hay un número limitado k de operarios disponibles con 3 estrategias de búsqueda diferentes.
- **Job Shop con Habilidades de Operarios**: Considera operarios especializados con habilidades específicas para ciertas tareas con 2 estrategias de búsqueda.
- **Job Shop con Mantenimiento**: Incluye ventanas de mantenimiento programado en las máquinas con 4 estrategias de búsqueda.

La herramienta proporciona:
- Interfaz web moderna con Bootstrap 5
- Selección progresiva: modelo → datos → configuración
- Tests precargados para cada modelo
- Visualización interactiva con diagramas de Gantt por máquinas usando Plotly
- Análisis de carga de operarios/trabajadores con métricas de desbalance
- Comparación de estrategias de búsqueda agrupadas por tipo de modelo
- Exportación de resultados en formato CSV y PDF profesional con información detallada

## Requisitos

- Python 3.8+
- MiniZinc 2.6+ instalado en el sistema
- Solvers compatibles: Gecode, Chuffed, COIN-BC

## Instalación

### Opción 1: Script automático (Recomendado)

```bash
chmod +x setup.sh
./setup.sh
```

El script automáticamente:
- Crea el entorno virtual
- Instala dependencias
- Detecta la instalación de MiniZinc
- Configura el archivo .env

### Opción 2: Manual

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd ProjectJobShop
```

2. Crear y activar entorno virtual:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. (Opcional) Configurar ruta de MiniZinc:
Si MiniZinc no está en tu PATH, crea un archivo `.env`:
```bash
echo "MINIZINC_BIN_PATH=/ruta/a/minizinc" > .env
```

4. Configurar MiniZinc (opcional):

Si MiniZinc no está en el PATH del sistema, crear un archivo `.env` en la raíz del proyecto con:
```
MINIZINC_BIN_PATH=/ruta/al/binario/de/minizinc
```

## Uso

1. Iniciar la aplicación:
```bash
python app.py
```

2. Abrir el navegador en `http://localhost:8080`

3. Seguir el flujo de trabajo:
   - **Paso 1**: Seleccionar modelo de optimización (tipo y estrategia de búsqueda)
   - **Paso 2**: Elegir datos del problema:
     - Opción A: Usar tests precargados (se cargan según el modelo seleccionado)
     - Opción B: Subir archivo `.dzn` personalizado
   - **Paso 3**: Configurar solver y tiempo límite
   - **Paso 4**: Ejecutar y visualizar resultados

## Estructura del Proyecto

```
ProjectJobShop/
├── app.py                  # Aplicación Flask principal
├── setup.sh                # Script de instalación automática
├── requirements.txt        # Dependencias Python
├── helpers/                # Módulos auxiliares
│   ├── minizinc_helper.py       # Operaciones con MiniZinc
│   ├── data_helper.py           # Parsing de archivos .dzn
│   ├── csv_helper.py            # Exportación CSV
│   ├── pdf_helper.py            # Generación de PDFs profesionales
│   └── visualization_helper.py  # Generación de gráficos Plotly
├── controllers/            # Controladores por tipo de modelo
│   ├── controller_oplimit.py    # Extracción de resultados op_limit
│   ├── controller_workers.py    # Extracción de resultados workers_skills
│   ├── controller_maintenance.py # Extracción de resultados maintenance
│   └── controller_comparison.py  # Comparación paralela de modelos
├── models/                 # Modelos MiniZinc organizados por tipo
│   ├── jobshop_op_limit/
│   │   ├── jobshop_op_limit_1.mzn  (Búsqueda libre)
│   │   ├── jobshop_op_limit_2.mzn  (dom_w_deg + first_fail)
│   │   ├── jobshop_op_limit_3.mzn  (Operario primero)
│   │   └── tests/          # Archivos de prueba .dzn
│   ├── jobshop_workers_skills/
│   │   ├── jobshop_workers_skills_1.mzn  (Búsqueda libre)
│   │   ├── jobshop_workers_skills_2.mzn  (dom_w_deg + first_fail)
│   │   └── tests/          # Archivos de prueba .dzn
│   └── jobshop_maintenance/
│       ├── jobshop_maintenance_1.mzn  (Solución directa)
│       ├── jobshop_maintenance_2.mzn  (First-fail)
│       ├── jobshop_maintenance_3.mzn  (Input order random)
│       ├── jobshop_maintenance_4.mzn  (Búsqueda por jobs)
│       └── tests/          # Archivos de prueba .dzn
├── templates/              # Templates HTML con Bootstrap 5
│   ├── layout.html         # Layout base con navbar y footer
│   ├── index.html          # Interfaz principal con flujo progresivo
│   ├── results.html        # Visualización de resultados
│   └── compare.html        # Comparación de estrategias
├── static/                 # Archivos estáticos
│   └── style.css           # Estilos personalizados compatibles con Bootstrap
└── uploads/                # Archivos cargados por usuarios (temporal)
```

## Modelos Disponibles

### 1. Job Shop con Operarios Limitados (10 tests)

Tres variaciones con diferentes estrategias de búsqueda:
1. **Búsqueda Libre**: Sin estrategia definida (explora naturalmente)
2. **dom_w_deg + first_fail**: Tiempo con dom_w_deg, operarios con first_fail
3. **Operario Primero**: Prioriza asignación de operarios antes que tiempos

**Formato de datos (.dzn):**
```minizinc
jobs = 5;
tasks = 5;
k = 3;  // número de operarios disponibles
d = [| 1,4,5,3,6
     | 3,2,7,1,2
     | 4,4,4,4,4
     | 1,1,1,6,8
     | 7,3,2,2,1 |];
```

### 2. Job Shop con Habilidades de Operarios (10 tests)

Dos variaciones para modelar operarios especializados:
1. **Búsqueda Libre**: Sin estrategia definida
2. **dom_w_deg + first_fail**: Tiempo con dom_w_deg, asignación con first_fail

**Formato de datos (.dzn):**
```minizinc
JOB = _(1..8);   // definición de jobs (puede ser rango o enumeración)
TASK = _(1..6);  // definición de tareas
d = [| 8, 7, 3, 6, 7, 4
     | 2, 7, 5, 8, 6, 8
     | 6, 1, 6, 4, 4, 7
     | 1, 1, 1, 2, 7, 3
     | 7, 3, 6, 5, 4, 5
     | 3, 7, 7, 5, 8, 5
     | 7, 5, 1, 8, 8, 3
     | 8, 7, 5, 1, 4, 2 |];
W = 4;  // número de trabajadores
skills = [
  {1,2,3,4},   % T1: trabajadores que pueden hacer tarea 1
  {1},         % T2: solo trabajador 1
  {1,3},       % T3: trabajadores 1 y 3
  {4},         % T4: solo trabajador 4
  {4},         % T5: solo trabajador 4
  {3}          % T6: solo trabajador 3
];
```

### 3. Job Shop con Mantenimiento (10 tests)

Cuatro variaciones con ventanas de mantenimiento en máquinas:
1. **Solución Directa**: Sin anotaciones de búsqueda
2. **First-Fail con indomain_min**: Estrategia first_fail
3. **Input Order Random**: Orden de entrada con valores aleatorios
4. **Búsqueda por Jobs**: Búsqueda secuencial por cada job

**Formato de datos (.dzn):**
```minizinc
jobs = 5;
tasks = 5;
d = [| 1, 4, 5, 3, 6
     | 3, 2, 7, 1, 2
     | 4, 4, 4, 4, 4
     | 1, 1, 1, 6, 8
     | 7, 3, 2, 2, 1 |];
% --- Mantenimientos ---
Nbreaks = 3;           // número de ventanas de mantenimiento
brk_m = [2, 3, 5];     // máquinas afectadas (número de tarea/columna)
brk_a = [3, 12, 8];    // inicio del paro
brk_b = [5, 15, 10];   // fin del paro (duración = brk_b - brk_a)
```

## Características

### Interfaz Moderna

- **Bootstrap 5**: Diseño responsivo y profesional
- **Bootstrap Icons**: Iconografía clara y consistente
- **Flujo progresivo**: Muestra opciones paso a paso
- **Tests precargados**: Selección dinámica según modelo elegido
- **Carga flexible**: Tests precargados o archivo personalizado

### Visualización

- **Diagrama de Gantt interactivo (Plotly)**: Muestra las máquinas en el eje Y y los jobs como barras de colores, permitiendo visualizar el uso de cada máquina en el tiempo
- **Tablas detalladas**: Tiempos de inicio organizados por Job y Máquina, con asignaciones de operarios/trabajadores
- **Progress bars**: Distribución de carga entre operarios/trabajadores con código de colores (rojo=máx, verde=mín)
- **Métricas clave**: Makespan, tiempo de ejecución, desbalance de carga, estado de solución
- **Comparación de estrategias**: Visualización agrupada por tipo de modelo con gráficos comparativos de makespan y desbalance

### Comparación de Modelos

- **Ejecución paralela**: Compara múltiples estrategias simultáneamente usando ThreadPoolExecutor
- **Agrupación por tipo**: Los resultados se organizan en categorías (Operarios Limitados, Habilidades, Mantenimiento)
- **Selección inteligente**: Solo permite comparar modelos del mismo tipo para resultados coherentes
- **Métricas específicas**: Muestra desbalance y carga solo para modelos que tienen operarios
- **Distribución de carga**: Visualiza la carga de cada operario/trabajador para comparar el balanceo entre estrategias

### Exportación

- Exportación de resultados en formatos CSV y PDF
- **CSV**: Incluye tiempos de inicio, duraciones y asignaciones en formato tabular
- **PDF**: Documentos profesionales con:
  - **Metadatos configurados** (título, autor, asunto) - no aparecen como "anonymous"
  - Información general y métricas de rendimiento
  - **Diagrama de Gantt interactivo exportado como imagen** (mismo gráfico que se ve en la web)
  - **Gráficos de comparación de makespan y desbalance** (en PDFs de comparación)
  - Tiempos de inicio y asignaciones detalladas
  - Distribución de carga con gráficos de barras
  - Comparaciones completas con rankings y análisis
- Nombres de archivo descriptivos según el tipo de modelo

### Solvers

La aplicación soporta múltiples solvers:
- **Gecode**: Solver por defecto, buen rendimiento general
- **Chuffed**: Especializado en problemas de satisfacción
- **COIN-BC**: Solver de programación lineal entera

## Archivos de Prueba

El directorio `models/<model_name>/tests/` contiene archivos de ejemplo:
- `data_01.dzn` - `data_05.dzn`: Instancias para habilidades de operarios

## Desarrollo

### Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Modelado**: MiniZinc
- **Visualización**: Plotly
- **Frontend**: HTML5, CSS3, JavaScript

### Agregar Nuevos Modelos

1. Crear archivo `.mzn` en `models/`
2. Agregar entrada en el diccionario `MODELS` en `app.py`
3. Definir tipo de modelo: `'op_limit'` o `'workers_skills'`
4. Opcionalmente ajustar procesamiento de resultados

## Licencia

Este proyecto es de código abierto bajo la licencia MIT.
