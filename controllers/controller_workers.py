"""
Controlador para modelos tipo workers_skills (Job Shop con habilidades de trabajadores)
"""
import minizinc
from helpers.minizinc_helper import extract_variable_flexible


def extract_workers_results(result, durations=None):
    """
    Extrae resultados específicos de modelos workers_skills
    
    Args:
        result: Resultado de MiniZinc
        durations: Matriz de duraciones (opcional, para calcular load si no está en resultado)
    
    Returns:
        Diccionario con resultados procesados
    """
    results = {}
    
    # Variables básicas siempre presentes
    results['start_times'] = [[int(result['s'][i][j]) for j in range(len(result['s'][i]))] 
                              for i in range(len(result['s']))]
    
    results['worker_assignment'] = [[int(result['w_assign'][i][j]) for j in range(len(result['w_assign'][i]))] 
                                     for i in range(len(result['w_assign']))]
    
    # Intentar obtener load del resultado, si no está, calcularlo
    try:
        results['worker_load'] = [int(x) for x in result['load']]
    except KeyError:
        # Calcular load manualmente usando assigned y durations
        try:
            if 'assigned' in result and durations is not None:
                assigned = result['assigned']
                
                # Determinar dimensiones desde assigned
                num_workers = len(assigned)
                num_jobs = len(durations) if durations else 0
                num_tasks = len(durations[0]) if durations and len(durations) > 0 else 0
                
                worker_load = []
                for w in range(num_workers):
                    load = 0
                    for i in range(num_jobs):
                        for j in range(num_tasks):
                            # assigned es array[WORKER, JOB, TASK] of var bool
                            if bool(assigned[w][i][j]):
                                load += durations[i][j]
                    worker_load.append(load)
                results['worker_load'] = worker_load
            else:
                # Si no podemos calcular, usar valores por defecto
                results['worker_load'] = []
        except (KeyError, IndexError, TypeError) as e:
            # Si falla el cálculo, intentar calcular desde w_assign
            try:
                w_assign = results['worker_assignment']
                num_jobs = len(w_assign)
                num_tasks = len(w_assign[0]) if num_jobs > 0 else 0
                
                # Determinar número de workers desde w_assign
                max_worker = max(max(row) for row in w_assign) if w_assign else 0
                num_workers = max_worker
                
                worker_load = [0] * num_workers
                for i in range(num_jobs):
                    for j in range(num_tasks):
                        worker_id = w_assign[i][j] - 1  # Convertir de 1-indexed a 0-indexed
                        if 0 <= worker_id < num_workers and durations:
                            worker_load[worker_id] += durations[i][j]
                
                results['worker_load'] = worker_load
            except Exception:
                results['worker_load'] = []
    
    # Intentar obtener maxLoad y minLoad, con fallback a calcular desde worker_load
    max_load = extract_variable_flexible(
        result,
        ['maxLoad', 'maxload', 'max_load'],
        lambda r: max(results['worker_load']) if results['worker_load'] else 0
    )
    results['max_load'] = max_load if max_load is not None else 0
    
    min_load = extract_variable_flexible(
        result,
        ['minLoad', 'minload', 'min_load'],
        lambda r: min(results['worker_load']) if results['worker_load'] else 0
    )
    results['min_load'] = min_load if min_load is not None else 0
    
    return results


def validate_workers_results(results):
    """
    Valida que los resultados de workers_skills sean consistentes
    
    Returns:
        True si válidos, False en caso contrario
    """
    required_keys = ['start_times', 'worker_assignment', 'worker_load', 
                     'max_load', 'min_load']
    
    return all(key in results for key in required_keys)
