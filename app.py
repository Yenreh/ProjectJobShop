"""
Job Shop Scheduling - Aplicación Flask
Aplicación web para resolver problemas de Job Shop Scheduling usando MiniZinc
"""
import os
import json
import datetime
import minizinc
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename

from helpers.data_helper import load_env, allowed_file, get_test_files, parse_durations_from_dzn, get_test_path_for_model
from helpers.minizinc_helper import solve_model
from helpers.visualization_helper import generate_gantt_chart, generate_comparison_chart, generate_imbalance_chart
from helpers.csv_helper import generate_single_result_csv, generate_comparison_csv
from controllers.controller_oplimit import extract_oplimit_results
from controllers.controller_workers import extract_workers_results
from controllers.controller_maintenance import extract_maintenance_results
from controllers.controller_comparison import run_comparison_parallel

load_env()

UPLOAD_FOLDER = 'uploads'
MODELS_FOLDER = 'models'
ALLOWED_EXTENSIONS = {'dzn'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MODELS_FOLDER'] = MODELS_FOLDER
app.config['SECRET_KEY'] = 'jobshop-scheduling-secret-key'

MODELS = {
    'jobshop_op_limit_1': {
        'name': 'Operarios Limitados - Búsqueda Libre',
        'file': 'jobshop_op_limit/jobshop_op_limit_1.mzn',
        'description': 'Job Shop con k operarios. Búsqueda sin seq_search.',
        'type': 'op_limit',
        'category': 'Operarios Limitados'
    },
    'jobshop_op_limit_2': {
        'name': 'Operarios Limitados - dom_w_deg + first_fail',
        'file': 'jobshop_op_limit/jobshop_op_limit_2.mzn',
        'description': 'Búsqueda: tiempo con dom_w_deg, operarios con first_fail.',
        'type': 'op_limit',
        'category': 'Operarios Limitados'
    },
    'jobshop_op_limit_3': {
        'name': 'Operarios Limitados - Operario Primero',
        'file': 'jobshop_op_limit/jobshop_op_limit_3.mzn',
        'description': 'Búsqueda: operario primero con first_fail.',
        'type': 'op_limit',
        'category': 'Operarios Limitados'
    },
    'jobshop_workers_skills_1': {
        'name': 'Habilidades de Operarios - Búsqueda Libre',
        'file': 'jobshop_workers_skills/jobshop_workers_skills_1.mzn',
        'description': 'Operarios especializados según habilidades. Búsqueda libre.',
        'type': 'workers_skills',
        'category': 'Habilidades de Operarios'
    },
    'jobshop_workers_skills_2': {
        'name': 'Habilidades de Operarios - dom_w_deg + first_fail',
        'file': 'jobshop_workers_skills/jobshop_workers_skills_2.mzn',
        'description': 'Búsqueda: tiempo con dom_w_deg, asignación con first_fail.',
        'type': 'workers_skills',
        'category': 'Habilidades de Operarios'
    },
    'jobshop_maintenance_1': {
        'name': 'Mantenimiento - Solución Directa',
        'file': 'jobshop_maintenance/jobshop_maintenance_1.mzn',
        'description': 'Job Shop con ventanas de mantenimiento. Búsqueda directa.',
        'type': 'maintenance',
        'category': 'Mantenimiento de Máquinas'
    },
    'jobshop_maintenance_2': {
        'name': 'Mantenimiento - First-Fail',
        'file': 'jobshop_maintenance/jobshop_maintenance_2.mzn',
        'description': 'Con mantenimiento. Búsqueda: first_fail con indomain_min.',
        'type': 'maintenance',
        'category': 'Mantenimiento de Máquinas'
    },
    'jobshop_maintenance_3': {
        'name': 'Mantenimiento - Input Order Random',
        'file': 'jobshop_maintenance/jobshop_maintenance_3.mzn',
        'description': 'Con mantenimiento. Búsqueda: input_order con indomain_random.',
        'type': 'maintenance',
        'category': 'Mantenimiento de Máquinas'
    },
    'jobshop_maintenance_4': {
        'name': 'Mantenimiento - Búsqueda por Jobs',
        'file': 'jobshop_maintenance/jobshop_maintenance_4.mzn',
        'description': 'Con mantenimiento. Búsqueda secuencial por cada job.',
        'type': 'maintenance',
        'category': 'Mantenimiento de Máquinas'
    }
}

SOLVERS = {
    'org.gecode.gecode': 'Gecode',
    'org.chuffed.chuffed': 'Chuffed',
    'org.minizinc.mip.coin-bc': 'COIN-BC',
    'org.minizinc.mip.highs': 'HiGHS',
}


@app.route('/')
def index():
    """Página principal"""
    uploaded_file = session.get('uploaded_file', None)
    uploaded_content = session.get('uploaded_content', None)
    
    # Obtener modelo de la URL o de la sesión
    selected_model = request.args.get('model', None) or session.get('selected_model', None)
    
    # Si viene de la URL, actualizar la sesión
    if request.args.get('model'):
        session['selected_model'] = selected_model
    
    model_info = MODELS.get(selected_model, None) if selected_model else None
    
    test_files = []
    if selected_model:
        test_files = get_test_files(app.config['MODELS_FOLDER'], selected_model, MODELS)
    
    return render_template('index.html', 
                          models=MODELS, 
                          solvers=SOLVERS,
                          uploaded_file=uploaded_file,
                          uploaded_content=uploaded_content,
                          dzn_content=uploaded_content,  # Agregar alias para template
                          selected_model=selected_model,
                          model_info=model_info,
                          test_files=test_files)


@app.route('/api/get_tests/<model_key>')
def get_tests(model_key):
    """API para obtener archivos de test de un modelo"""
    test_files = get_test_files(app.config['MODELS_FOLDER'], model_key, MODELS)
    return {'tests': test_files}


@app.route('/api/clear_test_data', methods=['POST'])
def clear_test_data():
    """API para limpiar datos de test cuando se cambia de modelo"""
    # Solo limpiar datos de archivo, mantener el modelo seleccionado
    session.pop('uploaded_file', None)
    session.pop('uploaded_content', None)
    session.pop('test_path', None)
    return {'status': 'ok'}


@app.route('/load_test', methods=['POST'])
def load_test():
    """Carga un archivo de test preconfigurado"""
    model_key = request.form.get('model')
    test_file = request.form.get('test_file')
    
    if not model_key or not test_file or model_key not in MODELS:
        flash('Modelo o archivo de test inválido.', 'error')
        return redirect(url_for('index'))
    
    model_info = MODELS[model_key]
    test_path = get_test_path_for_model(app.config['MODELS_FOLDER'], model_info['type'], test_file)
    
    if not os.path.exists(test_path):
        flash(f'Archivo de test no encontrado: {test_file}', 'error')
        return redirect(url_for('index'))
    
    with open(test_path, 'r') as f:
        content = f.read()
    
    session['uploaded_file'] = test_file
    session['uploaded_content'] = content
    session['selected_model'] = model_key
    session['test_path'] = test_path
    
    flash(f'Test cargado: {test_file}', 'success')
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload_file():
    """Maneja la subida de archivos .dzn"""
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        session['uploaded_file'] = filename
        session['uploaded_content'] = content
        session['uploaded_path'] = filepath
        
        flash(f'Archivo subido correctamente: {filename}', 'success')
        return redirect(url_for('index'))
    
    flash('Tipo de archivo no permitido. Solo se aceptan archivos .dzn', 'error')
    return redirect(url_for('index'))


@app.route('/run_model', methods=['POST'])
def run_model():
    """Ejecuta el modelo seleccionado con los datos cargados"""
    model_key = request.form.get('model')
    solver_key = request.form.get('solver', 'org.gecode.gecode')
    timeout = int(request.form.get('timeout', 60))
    
    if model_key not in MODELS:
        flash('Modelo no válido.', 'error')
        return redirect(url_for('index'))
    
    uploaded_file = session.get('uploaded_file')
    data_path = session.get('test_path') or session.get('uploaded_path')
    
    if not data_path or not os.path.exists(data_path):
        flash('Debes cargar un archivo de datos primero.', 'error')
        return redirect(url_for('index'))
    
    model_info = MODELS[model_key]
    model_path = os.path.join(app.config['MODELS_FOLDER'], model_info['file'])
    
    try:
        result = solve_model(model_path, data_path, solver_key, timeout)
        
        if result.status in [minizinc.Status.OPTIMAL_SOLUTION, minizinc.Status.SATISFIED, minizinc.Status.ALL_SOLUTIONS]:
            solve_time_delta = result.statistics.get('solveTime', datetime.timedelta(0))
            execution_time = solve_time_delta.total_seconds()
            
            results = {
                'status': str(result.status).replace('Status.', ''),
                'makespan': result['end'],
                'execution_time': f"{execution_time:.4f} segundos",
                'model_name': model_info['name'],
                'model_type': model_info['type'],
                'solver': SOLVERS.get(solver_key, solver_key),
                'data_file': uploaded_file
            }
            
            # Leer duraciones primero para los modelos que las necesiten
            with open(data_path, 'r') as f:
                dzn_lines = f.read()
            durations = parse_durations_from_dzn(dzn_lines)
            results['durations'] = durations
            
            if model_info['type'] == 'op_limit':
                specific_results = extract_oplimit_results(result)
                results.update(specific_results)
            
            elif model_info['type'] == 'workers_skills':
                specific_results = extract_workers_results(result, durations)
                results.update(specific_results)
            
            elif model_info['type'] == 'maintenance':
                specific_results = extract_maintenance_results(result)
                results.update(specific_results)
            
            session['results'] = results
            flash(f'Modelo ejecutado exitosamente. Makespan: {results["makespan"]}', 'success')
            return redirect(url_for('show_results'))
        
        elif result.status == minizinc.Status.UNSATISFIABLE:
            flash('El modelo no tiene solución (UNSATISFIABLE). Verifica los datos de entrada.', 'warning')
        elif result.status == minizinc.Status.UNKNOWN:
            flash('No se encontró solución en el tiempo límite. Intenta aumentar el timeout.', 'warning')
        else:
            flash(f'Estado inesperado: {result.status}', 'warning')
        
        return redirect(url_for('index'))
    
    except minizinc.MiniZincError as e:
        error_msg = str(e)
        if 'syntax error' in error_msg.lower():
            flash(f'Error de sintaxis en el archivo .dzn o modelo: {error_msg}', 'error')
        elif 'type error' in error_msg.lower():
            flash(f'Error de tipos en el modelo o datos: {error_msg}', 'error')
        else:
            flash(f'Error de MiniZinc: {error_msg}', 'error')
        return redirect(url_for('index'))
    
    except FileNotFoundError as e:
        flash(f'Archivo no encontrado: {e}', 'error')
        return redirect(url_for('index'))
    
    except KeyError as e:
        flash(f'Variable esperada no encontrada en la solución: {e}. Verifica que el modelo y los datos sean compatibles.', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error inesperado: {type(e).__name__}: {e}', 'error')
        return redirect(url_for('index'))


@app.route('/results')
def show_results():
    """Muestra los resultados de la optimización"""
    results = session.get('results', None)
    if not results:
        flash('No hay resultados para mostrar.', 'info')
        return redirect(url_for('index'))
    
    gantt_html = generate_gantt_chart(results)
    results['gantt_chart'] = gantt_html
    
    return render_template('results.html', results=results)


@app.route('/export_csv')
def export_csv():
    """Exporta los resultados a CSV"""
    results = session.get('results', None)
    if not results:
        flash('No hay resultados para exportar.', 'error')
        return redirect(url_for('index'))
    
    csv_content = generate_single_result_csv(results)
    model_type = results.get('model_type', 'jobshop')
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-disposition': f'attachment; filename=jobshop_{model_type}_results.csv'}
    )


@app.route('/clear')
def clear_session():
    """Limpia la sesión actual"""
    session.clear()
    flash('Sesión limpiada.', 'info')
    return redirect(url_for('index'))


@app.route('/compare')
def compare():
    """Página de comparación de estrategias"""
    return render_template('compare.html', models=MODELS, solvers=SOLVERS, comparison_results=None)


@app.route('/run_comparison', methods=['POST'])
def run_comparison():
    """Ejecuta comparación de múltiples modelos"""
    test_filename = request.form.get('test_file')
    solver_key = request.form.get('solver', 'org.gecode.gecode')
    timeout = int(request.form.get('timeout', 60))
    selected_models = request.form.getlist('models')
    
    if not test_filename or not selected_models or len(selected_models) < 2:
        flash('Debes seleccionar un test y al menos 2 modelos para comparar.', 'error')
        return redirect(url_for('compare'))
    
    results_list = run_comparison_parallel(
        selected_models, 
        test_filename, 
        solver_key, 
        timeout, 
        MODELS,
        app.config['MODELS_FOLDER']
    )
    
    if not results_list:
        flash('No se obtuvieron resultados de la comparación.', 'error')
        return redirect(url_for('compare'))
    
    chart_html = generate_comparison_chart(results_list)
    imbalance_chart_html = generate_imbalance_chart(results_list)
    
    comparison_results = {
        'test_file': test_filename,
        'solver': SOLVERS.get(solver_key, solver_key),
        'results': results_list,
        'chart': chart_html,
        'imbalance_chart': imbalance_chart_html
    }
    
    session['comparison_results'] = comparison_results
    
    flash(f'Comparación completada. Mejor resultado: {results_list[0]["model_name"]} con makespan {results_list[0]["makespan"]}', 'success')
    
    return render_template('compare.html', models=MODELS, solvers=SOLVERS, comparison_results=comparison_results)


@app.route('/export_comparison_csv')
def export_comparison_csv():
    """Exporta resultados de comparación a CSV"""
    comparison_results = session.get('comparison_results', None)
    if not comparison_results:
        flash('No hay resultados de comparación para exportar.', 'error')
        return redirect(url_for('compare'))
    
    csv_content = generate_comparison_csv(comparison_results)
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-disposition': f'attachment; filename=comparison_{comparison_results["test_file"]}.csv'}
    )


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=8080)
