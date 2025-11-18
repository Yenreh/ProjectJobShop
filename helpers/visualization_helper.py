"""
Helper para generación de visualizaciones (gráficos de Gantt y comparaciones)
"""
import plotly.graph_objects as go


def generate_gantt_chart(results):
    """
    Genera un diagrama de Gantt interactivo con Plotly
    Muestra las máquinas en el eje Y y los trabajos como barras coloreadas
    
    Args:
        results: Diccionario con resultados del modelo
    
    Returns:
        HTML string del gráfico de Gantt
    """
    start_times = results.get('start_times', [])
    durations = results.get('durations', [])
    
    if not start_times or not durations:
        return '<p>No se pudo generar el diagrama de Gantt.</p>'
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    model_type = results.get('model_type', 'op_limit')
    
    # Rastrear qué jobs ya se mostraron en la leyenda
    jobs_shown = set()
    
    # Iterar por cada job y cada máquina
    for job_idx, (start_row, duration_row) in enumerate(zip(start_times, durations)):
        
        for task_idx, (start, duration) in enumerate(zip(start_row, duration_row)):
            color = colors[job_idx % len(colors)]
            
            # El eje Y representa las máquinas
            y_label = f'Máquina {task_idx+1}'
            
            if model_type == 'op_limit':
                operator = results['operator_assignment'][job_idx][task_idx]
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Operario: {operator}<br>Inicio: {start}<br>Duración: {duration}'
            elif model_type == 'workers_skills':
                worker = results['worker_assignment'][job_idx][task_idx]
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Trabajador: {worker}<br>Inicio: {start}<br>Duración: {duration}'
            else:
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Inicio: {start}<br>Duración: {duration}'
            
            # Mostrar en leyenda solo la primera vez que aparece cada job
            show_in_legend = job_idx not in jobs_shown
            if show_in_legend:
                jobs_shown.add(job_idx)
            
            fig.add_trace(go.Bar(
                x=[duration],
                y=[y_label],
                orientation='h',
                base=start,
                marker=dict(color=color, line=dict(color='white', width=1)),
                name=f'Job {job_idx+1}',
                showlegend=show_in_legend,
                text=f'J{job_idx+1}',
                textposition='inside',
                hovertext=hover_text,
                hoverinfo='text',
                legendgroup=f'Job {job_idx+1}'
            ))
    
    num_machines = len(durations[0]) if durations else 0
    
    fig.update_layout(
        title='Diagrama de Gantt - Job Shop Scheduling (por Máquina)',
        xaxis_title='Tiempo',
        yaxis_title='Máquinas',
        barmode='overlay',
        height=max(400, 150 + num_machines * 50),
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title="Jobs",
            traceorder="normal"
        ),
        yaxis=dict(autorange='reversed'),
        template='plotly_white'
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def generate_comparison_chart(results_list):
    """Genera gráfico de barras comparativo de makespan"""
    fig = go.Figure()
    
    valid_results = [r for r in results_list if r['success']]
    
    if not valid_results:
        return '<p>No hay resultados válidos para mostrar.</p>'
    
    fig.add_trace(go.Bar(
        x=[r['model_name'] for r in valid_results],
        y=[r['makespan'] for r in valid_results],
        text=[r['makespan'] for r in valid_results],
        textposition='auto',
        marker=dict(color=['#28a745' if i == 0 else '#007bff' for i in range(len(valid_results))]),
        hovertemplate='<b>%{x}</b><br>Makespan: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Comparación de Makespan por Estrategia',
        xaxis_title='Modelo / Estrategia',
        yaxis_title='Makespan (unidades de tiempo)',
        height=450,
        showlegend=False,
        xaxis={
            'tickangle': -45,
            'automargin': True
        },
        margin=dict(l=50, r=50, t=80, b=120),
        template='plotly_white'
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def generate_imbalance_chart(results_list):
    """Genera gráfico de barras comparativo de desbalance"""
    valid_results = [r for r in results_list if r['success'] and r.get('imbalance') is not None]
    
    if not valid_results:
        return '<p>No hay datos de desbalance disponibles.</p>'
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[r['model_name'] for r in valid_results],
        y=[r['imbalance'] for r in valid_results],
        text=[r['imbalance'] for r in valid_results],
        textposition='auto',
        marker=dict(
            color=[r['imbalance'] for r in valid_results],
            colorscale=[[0, '#28a745'], [0.5, '#ffc107'], [1, '#dc3545']],
            showscale=True,
            colorbar=dict(title="Desbalance")
        ),
        hovertemplate='<b>%{x}</b><br>Desbalance: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Comparación de Desbalance de Carga',
        xaxis_title='Modelo / Estrategia',
        yaxis_title='Desbalance (Max - Min)',
        height=450,
        showlegend=False,
        xaxis={
            'tickangle': -45,
            'automargin': True
        },
        margin=dict(l=50, r=80, t=80, b=120),
        template='plotly_white'
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
