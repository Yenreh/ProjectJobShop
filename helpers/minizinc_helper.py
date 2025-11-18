"""
Helper para operaciones con MiniZinc
"""
import os
import minizinc
import datetime
from pathlib import Path


def configure_minizinc_driver():
    """Configura el driver de MiniZinc desde variable de entorno"""
    if 'MINIZINC_BIN_PATH' in os.environ:
        bin_path = Path(os.environ['MINIZINC_BIN_PATH'])
        if bin_path.is_dir():
            minizinc_exe = bin_path / 'minizinc'
            if minizinc_exe.exists():
                driver = minizinc.Driver(minizinc_exe)
                minizinc.default_driver = driver
        elif bin_path.exists():
            driver = minizinc.Driver(bin_path)
            minizinc.default_driver = driver


def get_solver(solver_key):
    """Obtiene un solver de MiniZinc, con fallback a Gecode"""
    try:
        return minizinc.Solver.lookup(solver_key)
    except LookupError:
        # Fallback al solver por defecto (Gecode)
        try:
            return minizinc.Solver.lookup('org.gecode.gecode')
        except LookupError:
            # Si tampoco está disponible, buscar cualquier solver
            raise Exception(f"No se pudo encontrar el solver '{solver_key}' ni el solver por defecto")


def solve_model(model_path, data_path, solver_key, timeout):
    """
    Ejecuta un modelo MiniZinc con los datos especificados
    
    Returns:
        result: Resultado de MiniZinc
    """
    configure_minizinc_driver()
    
    model = minizinc.Model(model_path)
    model.add_file(data_path)
    
    solver = get_solver(solver_key)
    instance = minizinc.Instance(solver, model)
    
    result = instance.solve(timeout=datetime.timedelta(seconds=timeout))
    return result


def extract_variable_flexible(result, possible_names, calculate_fn=None):
    """
    Extrae una variable del resultado intentando múltiples nombres
    
    Args:
        result: Resultado de MiniZinc
        possible_names: Lista de posibles nombres de la variable
        calculate_fn: Función opcional para calcular el valor si no se encuentra
    
    Returns:
        Valor de la variable o None si no se encuentra
    """
    for name in possible_names:
        try:
            return int(result[name])
        except (KeyError, AttributeError):
            continue
    
    if calculate_fn:
        return calculate_fn(result)
    
    return None
