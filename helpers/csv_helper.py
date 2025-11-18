"""
Helper para exportación de resultados a CSV
"""


def generate_single_result_csv(results):
    """
    Genera CSV para resultados de un solo modelo
    
    Args:
        results: Diccionario con resultados del modelo
    
    Returns:
        String con contenido CSV
    """
    csv_lines = []
    model_type = results.get('model_type', 'op_limit')
    
    # Agregar explicación del formato
    csv_lines.append('=== JOB SHOP SCHEDULING - RESULTADOS ===')
    csv_lines.append('Nota: Cada tarea de un job se ejecuta en una maquina especifica (Tarea/Maquina)')
    csv_lines.append('Ejemplo: Job 1 Tarea/Maquina 2 significa la segunda operacion del Job 1 que se ejecuta en la Maquina 2')
    csv_lines.append('')
    
    if model_type == 'op_limit':
        csv_lines.append('Job,Tarea/Maquina,Inicio,Duracion,Operario')
    elif model_type == 'workers_skills':
        csv_lines.append('Job,Tarea/Maquina,Inicio,Duracion,Trabajador')
    else:
        csv_lines.append('Job,Tarea/Maquina,Inicio,Duracion')
    
    start_times = results.get('start_times', [])
    durations = results.get('durations', [])
    
    if model_type == 'op_limit':
        assignments = results.get('operator_assignment', [])
        for job_idx, (start_row, duration_row, assign_row) in enumerate(zip(start_times, durations, assignments)):
            for task_idx, (start, duration, assign) in enumerate(zip(start_row, duration_row, assign_row)):
                csv_lines.append(f'{job_idx+1},{task_idx+1},{start},{duration},{assign}')
    
    elif model_type == 'workers_skills':
        assignments = results.get('worker_assignment', [])
        for job_idx, (start_row, duration_row, assign_row) in enumerate(zip(start_times, durations, assignments)):
            for task_idx, (start, duration, assign) in enumerate(zip(start_row, duration_row, assign_row)):
                csv_lines.append(f'{job_idx+1},{task_idx+1},{start},{duration},{assign}')
    
    else:
        for job_idx, (start_row, duration_row) in enumerate(zip(start_times, durations)):
            for task_idx, (start, duration) in enumerate(zip(start_row, duration_row)):
                csv_lines.append(f'{job_idx+1},{task_idx+1},{start},{duration}')
    
    csv_lines.append('')
    csv_lines.append('=== RESUMEN ===')
    csv_lines.append(f'Modelo,{results["model_name"]}')
    csv_lines.append(f'Tipo,{model_type}')
    csv_lines.append(f'Makespan,{results["makespan"]}')
    csv_lines.append(f'Tiempo de ejecucion,{results["execution_time"]}')
    csv_lines.append(f'Solver,{results["solver"]}')
    csv_lines.append(f'Archivo de datos,{results["data_file"]}')
    
    if model_type == 'op_limit':
        csv_lines.append('')
        csv_lines.append('=== CARGA DE OPERARIOS ===')
        csv_lines.append('Operario,Carga')
        for idx, load in enumerate(results.get('operator_load', [])):
            csv_lines.append(f'{idx+1},{load}')
        csv_lines.append(f'Carga Maxima,{results.get("max_load", "N/A")}')
        csv_lines.append(f'Carga Minima,{results.get("min_load", "N/A")}')
        csv_lines.append(f'Desbalance,{results.get("imbalance", "N/A")}')
    
    elif model_type == 'workers_skills':
        csv_lines.append('')
        csv_lines.append('=== CARGA DE TRABAJADORES ===')
        worker_load = results.get('worker_load', [])
        if worker_load:
            csv_lines.append('Trabajador,Carga')
            for idx, load in enumerate(worker_load, 1):
                csv_lines.append(f'{idx},{load}')
            csv_lines.append(f'Carga Maxima,{results.get("max_load", "N/A")}')
            csv_lines.append(f'Carga Minima,{results.get("min_load", "N/A")}')
            desbalance = results.get('max_load', 0) - results.get('min_load', 0)
            csv_lines.append(f'Desbalance,{desbalance}')
        else:
            csv_lines.append('No hay datos de carga disponibles')
    
    return '\n'.join(csv_lines)


def generate_comparison_csv(comparison_results):
    """
    Genera CSV para resultados de comparación
    
    Args:
        comparison_results: Diccionario con resultados de comparación
    
    Returns:
        String con contenido CSV
    """
    csv_lines = []
    csv_lines.append('=== COMPARACIÓN DE MODELOS ===')
    csv_lines.append(f'Archivo de test,{comparison_results["test_file"]}')
    csv_lines.append(f'Solver,{comparison_results["solver"]}')
    csv_lines.append(f'Modelos comparados,{len(comparison_results["results"])}')
    csv_lines.append('')
    
    csv_lines.append('Ranking,Categoria,Modelo,Tipo,Makespan,Tiempo(seg),Desbalance,Carga Max,Carga Min,Num Operarios/Trabajadores,Estado')
    
    for idx, result in enumerate(comparison_results['results'], 1):
        ranking = f'#{idx}' if idx > 1 else 'GANADOR'
        categoria = result.get('category', 'N/A')
        modelo = result.get('model_name', 'N/A')
        tipo = result.get('model_type', 'N/A')
        makespan = result.get('makespan', 'N/A')
        tiempo = result.get('execution_time', 'N/A')
        
        # Calcular desbalance según el tipo de modelo
        if tipo == 'op_limit':
            desbalance = result.get('imbalance', 'N/A')
            max_load = result.get('max_load', 'N/A')
            min_load = result.get('min_load', 'N/A')
            num_workers = result.get('num_operators', len(result.get('operator_load', [])))
        elif tipo == 'workers_skills':
            max_load = result.get('max_load', 'N/A')
            min_load = result.get('min_load', 'N/A')
            # Calcular desbalance si tenemos max y min
            if max_load != 'N/A' and min_load != 'N/A':
                desbalance = max_load - min_load
            else:
                desbalance = 'N/A'
            num_workers = result.get('num_workers', len(result.get('worker_load', [])))
        else:  # maintenance
            desbalance = 'N/A'
            max_load = 'N/A'
            min_load = 'N/A'
            num_workers = 'N/A'
        
        status = result.get('status', 'N/A')
        
        csv_lines.append(f'{ranking},{categoria},{modelo},{tipo},{makespan},{tiempo},{desbalance},{max_load},{min_load},{num_workers},{status}')
    
    # Agregar detalles de carga por modelo
    for idx, result in enumerate(comparison_results['results'], 1):
        tipo = result.get('model_type', 'N/A')
        
        if tipo == 'op_limit' and result.get('operator_load'):
            csv_lines.append('')
            csv_lines.append(f'=== {result["model_name"]} - DISTRIBUCIÓN DE CARGA ===')
            csv_lines.append('Operario,Carga')
            for op_idx, load in enumerate(result['operator_load'], 1):
                csv_lines.append(f'{op_idx},{load}')
            csv_lines.append(f'Desbalance,{result.get("imbalance", "N/A")}')
        
        elif tipo == 'workers_skills' and result.get('worker_load'):
            csv_lines.append('')
            csv_lines.append(f'=== {result["model_name"]} - DISTRIBUCIÓN DE CARGA ===')
            csv_lines.append('Trabajador,Carga')
            for w_idx, load in enumerate(result['worker_load'], 1):
                csv_lines.append(f'{w_idx},{load}')
            max_load = result.get('max_load')
            min_load = result.get('min_load')
            if max_load is not None and min_load is not None:
                csv_lines.append(f'Desbalance,{max_load - min_load}')
    
    return '\n'.join(csv_lines)
