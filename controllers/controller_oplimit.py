"""
Controlador para modelos tipo op_limit (Job Shop con límite de operarios)
"""
import minizinc
from helpers.minizinc_helper import extract_variable_flexible


def extract_oplimit_results(result):
    """
    Extrae resultados específicos de modelos op_limit
    
    Args:
        result: Resultado de MiniZinc
    
    Returns:
        Diccionario con resultados procesados
    """
    results = {}
    
    results['start_times'] = [[int(result['s'][i][j]) for j in range(len(result['s'][i]))] 
                              for i in range(len(result['s']))]
    
    results['operator_assignment'] = [[int(result['o'][i][j]) for j in range(len(result['o'][i]))] 
                                       for i in range(len(result['o']))]
    
    results['operator_load'] = [int(x) for x in result['carga']]
    
    max_load = extract_variable_flexible(
        result,
        ['maxload', 'maxLoad', 'max_load', 'maxCarga'],
        lambda r: max(results['operator_load'])
    )
    results['max_load'] = max_load
    
    min_load = extract_variable_flexible(
        result,
        ['minload', 'minLoad', 'min_load', 'minCarga'],
        lambda r: min(results['operator_load'])
    )
    results['min_load'] = min_load
    results['imbalance'] = max_load - min_load
    
    return results


def validate_oplimit_results(results):
    """
    Valida que los resultados de op_limit sean consistentes
    
    Returns:
        True si válidos, False en caso contrario
    """
    required_keys = ['start_times', 'operator_assignment', 'operator_load', 
                     'max_load', 'min_load', 'imbalance']
    
    return all(key in results for key in required_keys)
