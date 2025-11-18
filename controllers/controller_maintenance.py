"""
Controlador para modelos tipo maintenance (Job Shop con mantenimiento de máquinas)
"""


def extract_maintenance_results(result):
    """
    Extrae resultados específicos de modelos maintenance
    
    Args:
        result: Resultado de MiniZinc
    
    Returns:
        Diccionario con resultados procesados
    """
    results = {}
    
    results['start_times'] = [[int(result['s'][i][j]) for j in range(len(result['s'][i]))] 
                              for i in range(len(result['s']))]
    
    return results


def validate_maintenance_results(results):
    """
    Valida que los resultados de maintenance sean consistentes
    
    Returns:
        True si válidos, False en caso contrario
    """
    required_keys = ['start_times']
    
    return all(key in results for key in required_keys)
