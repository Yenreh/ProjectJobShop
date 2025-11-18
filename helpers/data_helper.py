"""
Helper para manipulación de datos y archivos
"""
import os
from pathlib import Path


def load_env():
    """Carga variables de entorno desde archivo .env"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def allowed_file(filename, allowed_extensions):
    """Verifica si un archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_test_files(models_folder, model_key, models_config):
    """Obtiene lista de archivos de test para un modelo específico"""
    if model_key not in models_config:
        return []
    
    model_info = models_config[model_key]
    model_folder = os.path.dirname(model_info['file'])
    tests_folder = os.path.join(models_folder, model_folder, 'tests')
    
    if not os.path.exists(tests_folder):
        return []
    
    test_files = [f for f in os.listdir(tests_folder) 
                  if f.endswith('.dzn')]
    test_files.sort()
    
    return test_files


def parse_durations_from_dzn(dzn_content):
    """
    Parsea la matriz de duraciones desde un archivo .dzn
    
    Args:
        dzn_content: Contenido del archivo .dzn como string
    
    Returns:
        Lista de listas con las duraciones por job y tarea
    """
    lines = dzn_content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('d =') or line.strip().startswith('duration ='):
            # La matriz puede estar en múltiples líneas
            matrix_str = line.split('=', 1)[1].strip()
            
            # Si la matriz no termina en esta línea, seguir leyendo
            j = i + 1
            while '|]' not in matrix_str and j < len(lines):
                matrix_str += ' ' + lines[j].strip()
                j += 1
            
            # Limpiar la cadena
            matrix_str = matrix_str.replace('[|', '').replace('|]', '').replace(';', '').strip()
            
            # Separar por | para obtener las filas
            rows = [row.strip() for row in matrix_str.split('|') if row.strip()]
            
            # Parsear cada fila
            durations = []
            for row in rows:
                # Eliminar espacios múltiples y separar por comas
                values = [int(x.strip()) for x in row.split(',') if x.strip()]
                if values:  # Solo agregar si tiene valores
                    durations.append(values)
            
            return durations
    
    return []


def get_test_path_for_model(models_folder, model_type, test_filename):
    """
    Obtiene la ruta completa del archivo de test según el tipo de modelo
    
    Args:
        models_folder: Carpeta base de modelos
        model_type: Tipo de modelo (op_limit, workers_skills, maintenance)
        test_filename: Nombre del archivo de test
    
    Returns:
        Ruta completa al archivo de test
    """
    folder_map = {
        'op_limit': 'jobshop_op_limit',
        'workers_skills': 'jobshop_workers_skills',
        'maintenance': 'jobshop_maintenance'
    }
    
    test_folder = folder_map.get(model_type, 'jobshop_op_limit')
    return os.path.join(models_folder, test_folder, 'tests', test_filename)
