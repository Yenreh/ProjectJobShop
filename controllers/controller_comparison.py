"""
Controlador para comparaciones de modelos
"""
import os
import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import minizinc

from helpers.minizinc_helper import solve_model
from helpers.data_helper import get_test_path_for_model, parse_durations_from_dzn
from controllers.controller_oplimit import extract_oplimit_results
from controllers.controller_workers import extract_workers_results
from controllers.controller_maintenance import extract_maintenance_results


def run_single_model_comparison(model_key, test_filename, solver_key, timeout, models_config, models_folder):
    """
    Ejecuta un modelo individual y retorna los resultados detallados
    
    Args:
        model_key: Clave del modelo en la configuración
        test_filename: Nombre del archivo de test
        solver_key: Solver a utilizar
        timeout: Timeout en segundos
        models_config: Configuración de modelos
        models_folder: Carpeta base de modelos
    
    Returns:
        Diccionario con resultados del modelo
    """
    if model_key not in models_config:
        return None
    
    model_info = models_config[model_key]
    model_path = os.path.join(models_folder, model_info['file'])
    model_type = model_info['type']
    
    test_path = get_test_path_for_model(models_folder, model_type, test_filename)
    
    if not os.path.exists(test_path):
        return {
            'model_key': model_key,
            'model_name': model_info['name'],
            'category': model_info['category'],
            'model_type': model_type,
            'makespan': float('inf'),
            'execution_time': 'N/A',
            'status': 'ERROR: Test file not found',
            'success': False,
            'error_detail': f'File not found: {test_path}'
        }
    
    try:
        result = solve_model(model_path, test_path, solver_key, timeout)
        
        if result.status in [minizinc.Status.OPTIMAL_SOLUTION, minizinc.Status.SATISFIED]:
            solve_time = result.statistics.get('solveTime', datetime.timedelta(0)).total_seconds()
            
            # Leer duraciones del archivo de test
            durations = None
            try:
                with open(test_path, 'r') as f:
                    dzn_content = f.read()
                durations = parse_durations_from_dzn(dzn_content)
            except Exception:
                pass
            
            result_data = {
                'model_key': model_key,
                'model_name': model_info['name'],
                'category': model_info['category'],
                'model_type': model_type,
                'makespan': int(result['end']),
                'execution_time': f'{solve_time:.4f}',
                'status': str(result.status).replace('Status.', ''),
                'success': True
            }
            
            if model_type == 'op_limit':
                try:
                    specific_results = extract_oplimit_results(result)
                    result_data.update(specific_results)
                    result_data['num_operators'] = len(specific_results['operator_load'])
                except Exception:
                    pass
            
            elif model_type == 'workers_skills':
                try:
                    specific_results = extract_workers_results(result, durations)
                    result_data.update(specific_results)
                    result_data['num_workers'] = len(specific_results['worker_load'])
                    if 'max_load' in specific_results and 'min_load' in specific_results:
                        result_data['imbalance'] = specific_results['max_load'] - specific_results['min_load']
                except Exception:
                    pass
            
            elif model_type == 'maintenance':
                try:
                    specific_results = extract_maintenance_results(result)
                    result_data.update(specific_results)
                except Exception:
                    pass
            
            return result_data
        else:
            return {
                'model_key': model_key,
                'model_name': model_info['name'],
                'category': model_info['category'],
                'model_type': model_type,
                'makespan': float('inf'),
                'execution_time': 'N/A',
                'status': str(result.status).replace('Status.', ''),
                'success': False
            }
    
    except Exception as e:
        return {
            'model_key': model_key,
            'model_name': model_info['name'],
            'category': model_info['category'],
            'model_type': model_type,
            'makespan': float('inf'),
            'execution_time': 'Error',
            'status': f'ERROR: {str(e)[:50]}',
            'success': False,
            'error_detail': traceback.format_exc()
        }


def run_comparison_parallel(selected_models, test_filename, solver_key, timeout, models_config, models_folder, max_workers=4):
    """
    Ejecuta comparación de múltiples modelos en paralelo
    
    Args:
        selected_models: Lista de claves de modelos a comparar
        test_filename: Nombre del archivo de test
        solver_key: Solver a utilizar
        timeout: Timeout en segundos
        models_config: Configuración de modelos
        models_folder: Carpeta base de modelos
        max_workers: Número máximo de workers paralelos
    
    Returns:
        Lista de resultados ordenada por makespan
    """
    results_list = []
    
    with ThreadPoolExecutor(max_workers=min(len(selected_models), max_workers)) as executor:
        future_to_model = {
            executor.submit(
                run_single_model_comparison, 
                model_key, 
                test_filename, 
                solver_key, 
                timeout,
                models_config,
                models_folder
            ): model_key
            for model_key in selected_models
        }
        
        for future in as_completed(future_to_model):
            model_key = future_to_model[future]
            try:
                result = future.result()
                if result:
                    results_list.append(result)
            except Exception as e:
                pass
    
    results_list.sort(key=lambda x: x['makespan'])
    return results_list
