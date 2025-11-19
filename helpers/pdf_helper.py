"""
Helper para generar PDFs de resultados del Job Shop Scheduler
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime
import plotly.graph_objects as go


def generate_gantt_figure(results):
    """
    Genera la figura de Plotly del diagrama de Gantt
    Retorna el objeto Figure de Plotly
    """
    start_times = results.get('start_times', [])
    durations = results.get('durations', [])
    
    if not start_times or not durations:
        return None
    
    fig = go.Figure()
    
    colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    model_type = results.get('model_type', 'op_limit')
    jobs_shown = set()
    
    for job_idx, (start_row, duration_row) in enumerate(zip(start_times, durations)):
        for task_idx, (start, duration) in enumerate(zip(start_row, duration_row)):
            color = colors_list[job_idx % len(colors_list)]
            y_label = f'Máquina {task_idx+1}'
            
            if model_type == 'op_limit':
                operator = results['operator_assignment'][job_idx][task_idx]
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Operario: {operator}<br>Inicio: {start}<br>Duración: {duration}'
            elif model_type == 'workers_skills':
                worker = results['worker_assignment'][job_idx][task_idx]
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Trabajador: {worker}<br>Inicio: {start}<br>Duración: {duration}'
            else:
                hover_text = f'Job {job_idx+1} en Máquina {task_idx+1}<br>Inicio: {start}<br>Duración: {duration}'
            
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
        template='plotly_white',
        font=dict(size=10)
    )
    
    return fig


def plotly_fig_to_image(fig, width=800, height=600):
    """
    Convierte una figura de Plotly a bytes de imagen PNG
    """
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return BytesIO(img_bytes)
    except Exception as e:
        print(f"Error generando imagen: {e}")
        return None


def generate_comparison_makespan_figure(results_list):
    """
    Genera la figura de Plotly para comparación de makespan
    """
    valid_results = [r for r in results_list if r.get('success', False)]
    
    if not valid_results:
        return None
    
    fig = go.Figure()
    
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
        template='plotly_white',
        font=dict(size=11)
    )
    
    return fig


def generate_comparison_imbalance_figure(results_list):
    """
    Genera la figura de Plotly para comparación de desbalance
    """
    valid_results = [r for r in results_list if r.get('success', False) and r.get('imbalance') is not None]
    
    if not valid_results:
        return None
    
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
        template='plotly_white',
        font=dict(size=11)
    )
    
    return fig


def generate_single_result_pdf(results):
    """
    Genera un PDF con los resultados de una ejecución individual
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        title=f"Resultados - {results.get('model_name', 'Job Shop')}",
        author="Job Shop Scheduler",
        subject=f"Resultados de optimización - {results.get('data_file', 'N/A')}"
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    
    title = Paragraph("Resultados de Optimización - Job Shop Scheduler", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    summary_data = [
        ['Información General', ''],
        ['Modelo:', results.get('model_name', 'N/A')],
        ['Estado:', results.get('status', 'N/A')],
        ['Archivo de Datos:', results.get('data_file', 'N/A')],
        ['Solver:', results.get('solver', 'N/A')],
        ['Fecha:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    metrics_data = [
        ['Métricas de Rendimiento', ''],
        ['Makespan (Tiempo Total):', str(results.get('makespan', 'N/A'))],
        ['Tiempo de Ejecución:', results.get('execution_time', 'N/A')],
    ]
    
    if results.get('imbalance') is not None:
        metrics_data.append(['Desbalance de Carga:', str(results.get('imbalance', 'N/A'))])
    if results.get('max_load') is not None:
        metrics_data.append(['Carga Máxima:', str(results.get('max_load', 'N/A'))])
    if results.get('min_load') is not None:
        metrics_data.append(['Carga Mínima:', str(results.get('min_load', 'N/A'))])
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 4*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Diagrama de Gantt", heading_style))
    
    gantt_fig = generate_gantt_figure(results)
    if gantt_fig:
        try:
            num_machines = len(results.get('durations', [[]])[0])
            img_height = max(400, 150 + num_machines * 50)
            img_bytes = plotly_fig_to_image(gantt_fig, width=900, height=img_height)
            
            if img_bytes:
                img = Image(img_bytes, width=6.5*inch, height=img_height/900*6.5*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
            else:
                note = Paragraph(
                    "<i>No se pudo generar la imagen del gráfico de Gantt. "
                    "Asegúrate de tener instalado kaleido: pip install kaleido</i>",
                    normal_style
                )
                story.append(note)
        except Exception as e:
            note = Paragraph(
                f"<i>Error al generar el gráfico de Gantt: {str(e)}</i>",
                normal_style
            )
            story.append(note)
    else:
        note = Paragraph(
            "<i>No hay datos disponibles para generar el diagrama de Gantt.</i>",
            normal_style
        )
        story.append(note)
    
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Tiempos de Inicio de Tareas", heading_style))
    
    start_times = results.get('start_times', [])
    if start_times:
        num_tasks = len(start_times[0]) if start_times else 0
        
        header = ['Job'] + [f'M{i+1}' for i in range(num_tasks)]
        table_data = [header]
        
        for idx, row in enumerate(start_times):
            table_data.append([f'Job {idx+1}'] + [str(t) for t in row])
        
        col_widths = [1*inch] + [0.8*inch] * num_tasks
        if len(col_widths) * 0.8 > 6.5:
            col_width = 6.5 / len(col_widths)
            col_widths = [col_width*inch] * len(col_widths)
        
        start_table = Table(table_data, colWidths=col_widths)
        start_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('BACKGROUND', (1, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        
        story.append(start_table)
        story.append(Spacer(1, 0.2*inch))
    
    model_type = results.get('model_type', '')
    
    if model_type == 'op_limit' and results.get('operator_assignment'):
        story.append(PageBreak())
        story.append(Paragraph("Asignación de Operarios", heading_style))
        
        operator_assignment = results.get('operator_assignment', [])
        if operator_assignment:
            num_tasks = len(operator_assignment[0]) if operator_assignment else 0
            
            header = ['Job'] + [f'M{i+1}' for i in range(num_tasks)]
            table_data = [header]
            
            for idx, row in enumerate(operator_assignment):
                table_data.append([f'Job {idx+1}'] + [f'Op {op}' for op in row])
            
            col_widths = [1*inch] + [0.8*inch] * num_tasks
            if len(col_widths) * 0.8 > 6.5:
                col_width = 6.5 / len(col_widths)
                col_widths = [col_width*inch] * len(col_widths)
            
            op_table = Table(table_data, colWidths=col_widths)
            op_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            
            story.append(op_table)
            story.append(Spacer(1, 0.2*inch))
        
        operator_load = results.get('operator_load', [])
        if operator_load:
            story.append(Paragraph("Carga de Operarios", heading_style))
            
            load_data = [['Operario', 'Carga', 'Porcentaje']]
            max_load = results.get('max_load', max(operator_load) if operator_load else 1)
            
            for idx, load in enumerate(operator_load):
                percentage = f"{(load / max_load * 100):.1f}%" if max_load > 0 else "0%"
                load_data.append([f'Operario {idx+1}', str(load), percentage])
            
            load_table = Table(load_data, colWidths=[2*inch, 2*inch, 2*inch])
            load_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            
            story.append(load_table)
    
    elif model_type == 'workers_skills' and results.get('worker_assignment'):
        story.append(PageBreak())
        story.append(Paragraph("Asignación de Trabajadores", heading_style))
        
        worker_assignment = results.get('worker_assignment', [])
        if worker_assignment:
            num_tasks = len(worker_assignment[0]) if worker_assignment else 0
            
            header = ['Job'] + [f'M{i+1}' for i in range(num_tasks)]
            table_data = [header]
            
            for idx, row in enumerate(worker_assignment):
                table_data.append([f'Job {idx+1}'] + [f'W {w}' for w in row])
            
            col_widths = [1*inch] + [0.8*inch] * num_tasks
            if len(col_widths) * 0.8 > 6.5:
                col_width = 6.5 / len(col_widths)
                col_widths = [col_width*inch] * len(col_widths)
            
            worker_table = Table(table_data, colWidths=col_widths)
            worker_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            
            story.append(worker_table)
            story.append(Spacer(1, 0.2*inch))
        
        worker_load = results.get('worker_load', [])
        if worker_load:
            story.append(Paragraph("Carga de Trabajadores", heading_style))
            
            load_data = [['Trabajador', 'Carga', 'Porcentaje']]
            max_load = results.get('max_load', max(worker_load) if worker_load else 1)
            
            for idx, load in enumerate(worker_load):
                percentage = f"{(load / max_load * 100):.1f}%" if max_load > 0 else "0%"
                load_data.append([f'Trabajador {idx+1}', str(load), percentage])
            
            load_table = Table(load_data, colWidths=[2*inch, 2*inch, 2*inch])
            load_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            
            story.append(load_table)
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer


def generate_comparison_pdf(comparison_results):
    """
    Genera un PDF con los resultados de comparación de múltiples modelos
    """
    buffer = BytesIO()
    test_file = comparison_results.get('test_file', 'N/A')
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        title=f"Comparación de Estrategias - {test_file}",
        author="Job Shop Scheduler",
        subject=f"Comparación de modelos con {test_file}"
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    title = Paragraph("Comparación de Estrategias - Job Shop Scheduler", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    info_data = [
        ['Información de la Comparación', ''],
        ['Archivo de Test:', comparison_results.get('test_file', 'N/A')],
        ['Solver:', comparison_results.get('solver', 'N/A')],
        ['Modelos Comparados:', str(len(comparison_results.get('results', [])))],
        ['Fecha:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    results_list = comparison_results.get('results', [])
    
    results_by_type = {}
    for result in results_list:
        model_type = result.get('model_type', 'unknown')
        if model_type not in results_by_type:
            results_by_type[model_type] = []
        results_by_type[model_type].append(result)
    
    type_names = {
        'op_limit': 'Operarios Limitados',
        'workers_skills': 'Habilidades de Operarios',
        'maintenance': 'Mantenimiento de Máquinas'
    }
    
    for model_type, results in results_by_type.items():
        story.append(Paragraph(type_names.get(model_type, model_type), heading_style))
        
        table_data = [['Rank', 'Modelo', 'Makespan', 'Tiempo (s)', 'Estado']]
        
        if model_type in ['op_limit', 'workers_skills']:
            table_data[0].extend(['Desbalance', 'Carga Max', 'Carga Min'])
        
        for idx, result in enumerate(results):
            row = [
                f'#{idx+1}' if result.get('success', False) else 'X',
                result.get('model_name', 'N/A'),
                str(result.get('makespan', '-')) if result.get('success', False) else '-',
                result.get('execution_time', 'N/A'),
                result.get('status', 'N/A')
            ]
            
            if model_type in ['op_limit', 'workers_skills']:
                imbalance = result.get('imbalance')
                max_load = result.get('max_load')
                min_load = result.get('min_load')
                
                row.append(str(imbalance) if imbalance is not None else 'N/A')
                row.append(str(max_load) if max_load is not None else 'N/A')
                row.append(str(min_load) if min_load is not None else 'N/A')
            
            table_data.append(row)
        
        if model_type in ['op_limit', 'workers_skills']:
            col_widths = [0.5*inch, 2.2*inch, 0.9*inch, 0.9*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch]
        else:
            col_widths = [0.5*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.5*inch]
        
        comparison_table = Table(table_data, colWidths=col_widths)
        
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]
        
        for idx, result in enumerate(results):
            if result.get('success', False) and idx == 0:
                style_commands.append(('BACKGROUND', (0, idx+1), (-1, idx+1), colors.lightgreen))
                style_commands.append(('FONTNAME', (0, idx+1), (-1, idx+1), 'Helvetica-Bold'))
            elif not result.get('success', False):
                style_commands.append(('BACKGROUND', (0, idx+1), (-1, idx+1), colors.lightpink))
            elif idx % 2 == 0:
                style_commands.append(('BACKGROUND', (0, idx+1), (-1, idx+1), colors.lightgrey))
        
        comparison_table.setStyle(TableStyle(style_commands))
        
        story.append(comparison_table)
        story.append(Spacer(1, 0.2*inch))
        
        successful_results = [r for r in results if r.get('success', False)]
        if successful_results and model_type in ['op_limit', 'workers_skills']:
            story.append(Paragraph(f"Distribución de Carga - {type_names.get(model_type)}", heading_style))
            
            for result in successful_results[:3]:
                operator_load = result.get('operator_load') or result.get('worker_load')
                if operator_load:
                    load_data = [['Recurso', 'Carga']]
                    prefix = 'Op' if result.get('operator_load') else 'W'
                    
                    for idx, load in enumerate(operator_load):
                        load_data.append([f'{prefix} {idx+1}', str(load)])
                    
                    story.append(Paragraph(f"<b>{result.get('model_name', 'N/A')}</b>", styles['Normal']))
                    
                    load_table = Table(load_data, colWidths=[2*inch, 2*inch])
                    load_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#95a5a6')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ]))
                    
                    story.append(load_table)
                    story.append(Spacer(1, 0.1*inch))
        
        if model_type != list(results_by_type.keys())[-1]:
            story.append(Spacer(1, 0.3*inch))
    
    # Agregar gráficos de comparación
    story.append(PageBreak())
    story.append(Paragraph("Gráficos Comparativos", heading_style))
    
    results_list = comparison_results.get('results', [])
    
    # Gráfico de Makespan
    makespan_fig = generate_comparison_makespan_figure(results_list)
    if makespan_fig:
        try:
            img_bytes = plotly_fig_to_image(makespan_fig, width=900, height=450)
            if img_bytes:
                img = Image(img_bytes, width=6.5*inch, height=3.25*inch)
                story.append(Paragraph("Comparación de Makespan", heading_style))
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            else:
                note = Paragraph(
                    "<i>No se pudo generar el gráfico de makespan. "
                    "Asegúrate de tener instalado kaleido: pip install kaleido</i>",
                    styles['Normal']
                )
                story.append(note)
        except Exception as e:
            note = Paragraph(
                f"<i>Error al generar gráfico de makespan: {str(e)}</i>",
                styles['Normal']
            )
            story.append(note)
    
    # Gráfico de Desbalance
    imbalance_fig = generate_comparison_imbalance_figure(results_list)
    if imbalance_fig:
        try:
            img_bytes = plotly_fig_to_image(imbalance_fig, width=900, height=450)
            if img_bytes:
                img = Image(img_bytes, width=6.5*inch, height=3.25*inch)
                story.append(Paragraph("Comparación de Desbalance de Carga", heading_style))
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
        except Exception as e:
            pass
    
    best_result = None
    for result in results_list:
        if result.get('success', False):
            if best_result is None or result.get('makespan', 999999) < best_result.get('makespan', 999999):
                best_result = result
    
    if best_result:
        story.append(PageBreak())
        story.append(Paragraph("Mejor Resultado Global", heading_style))
        
        best_data = [
            ['Mejor Resultado', ''],
            ['Modelo:', best_result.get('model_name', 'N/A')],
            ['Makespan:', str(best_result.get('makespan', 'N/A'))],
            ['Tiempo de Ejecución:', best_result.get('execution_time', 'N/A')],
            ['Estado:', best_result.get('status', 'N/A')],
        ]
        
        if best_result.get('imbalance') is not None:
            best_data.append(['Desbalance:', str(best_result.get('imbalance', 'N/A'))])
        
        best_table = Table(best_data, colWidths=[2.5*inch, 4*inch])
        best_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef5e7')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(best_table)
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer
