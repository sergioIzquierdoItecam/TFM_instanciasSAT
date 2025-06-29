import matplotlib.pyplot as plt
import pandas as pd
import re
from itertools import cycle
from collections import defaultdict
from tabulate import tabulate

def parse_results_file(filename):
    """Analiza el archivo de resultados y devuelve un DataFrame"""
    data = []
    current_section = {}
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detectar encabezados de sección
            if line.startswith('####################'):
                param = line.strip('#').strip()
                if 'n =' in param:
                    current_section['n'] = int(re.search(r'n = (\d+)', param).group(1))
                elif 'c =' in param:
                    current_section['c'] = int(re.search(r'c = (\d+)', param).group(1))
                elif 'Q =' in param:
                    current_section['Q'] = float(re.search(r'Q = (\d+\.\d+)', param).group(1))
                elif 'Max Flips =' in param:
                    current_section['Max Flips'] = int(re.search(r'Max Flips = (\d+)', param).group(1))
            
            # Analizar líneas de datos
            elif line.startswith('c=') or line.startswith('n=') or line.startswith('p='):
                parts = re.split(r',\s+', line)
                entry = current_section.copy()
                
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key in ['n', 'c', 'max_tries']:
                            entry[key] = int(value)
                        elif key in ['Q', 'p', 'm/n']:
                            entry[key] = float(value)
                        elif key == 'max_flips':
                            entry['max_flips'] = int(value)

                    elif ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'Success Rate':
                            entry['Success Rate'] = float(value.rstrip('%'))
                        elif key == 'Total Flips':
                            entry['Total Flips'] = int(value)
                        elif key == 'Time':
                            entry['Time'] = float(value.split()[0])
                
                data.append(entry)
    
    return pd.DataFrame(data)

def generate_subplot(ax, group, hue_param, hue_value, fixed_params):
    """Genera un subgráfico individual y devuelve métricas cuantitativas"""
    colors = cycle(plt.cm.tab10.colors)
    markers = cycle(['o', 's', '^', 'D', 'v', 'p', '*', 'h', '8', 'X'])
    
    # Agrupar por el parámetro de hue si es diferente a los parámetros fijos
    plot_param = hue_param if hue_param not in fixed_params else None
    grouped = group.groupby(plot_param) if plot_param else [(None, group)]

    # Diccionario para almacenar métricas cuantitativas
    metrics = {
        'all': {},  # Métricas para todos los n combinados
        'by_n': defaultdict(dict)  # Métricas desglosadas por n
    }
    
    for (plot_value, subgroup), color, marker in zip(grouped, colors, markers):
        subgroup = subgroup.sort_values('m/n')
        label = f"{plot_param}={plot_value}" if plot_value else "All"
        
        # Calcular métricas generales (todos los n combinados)
        metrics['all'] = {
            'avg_success': group['Success Rate'].mean(),
            'max_success': group['Success Rate'].max(),
            'min_success': group['Success Rate'].min(),
            'avg_time': group['Time'].mean(),
            'avg_total_flips': group['Total Flips'].mean()  # Nueva métrica
        }
        
        # Encontrar el punto de transición de fase general
        critical_points = group[group['Success Rate'] < 50]['m/n']
        if not critical_points.empty:
            metrics['all']['phase_transition'] = critical_points.min()
        
        # Calcular métricas para cada valor de n
        for n, n_group in subgroup.groupby('n'):
            metrics['by_n'][n] = {
                'avg_success': n_group['Success Rate'].mean(),
                'max_success': n_group['Success Rate'].max(),
                'min_success': n_group['Success Rate'].min(),
                'avg_time': n_group['Time'].mean(),
                'avg_total_flips': n_group['Total Flips'].mean()  # Nueva métrica
            }
            
            # Punto de transición para este n específico
            n_critical_points = n_group[n_group['Success Rate'] < 50]['m/n']
            if not n_critical_points.empty:
                metrics['by_n'][n]['phase_transition'] = n_critical_points.min()
        
        ax.plot(
            subgroup['m/n'], 
            subgroup['Success Rate'], 
            label=label,
            color=color,
            marker=marker,
            linestyle='--',
            linewidth=1.5,
            markersize=5
        )
    
    # Título del subgráfico
    title_parts = []
    for param, value in fixed_params.items():
        if param != hue_param:
            title_parts.append(f"{param}={value}")
    if hue_param in fixed_params:
        title_parts.append(f"{hue_param}={hue_value}")
    
    ax.set_title(", ".join(title_parts), fontsize=10)
    ax.set_xlabel("m/n", fontsize=8)
    ax.set_ylabel("Success Rate (%)", fontsize=8)
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc='upper right')

    return metrics, ", ".join(title_parts)

def generate_metrics_tables(all_metrics, output_file=None):
    """Genera dos tablas comparativas: una general y otra desglosada por n"""
    # Preparar datos para ambas tablas
    general_data = []
    detailed_data = []
    
    for config, metrics in all_metrics.items():
        # Añadir a tabla general
        general_row = {
            'Configuration': config,
            **metrics['all']
        }
        general_data.append(general_row)
        
        # Añadir a tabla detallada
        for n, n_metrics in metrics['by_n'].items():
            detailed_row = {
                'Configuration': config,
                'n': n,
                **n_metrics
            }
            detailed_data.append(detailed_row)
    
    # Crear DataFrames
    df_general = pd.DataFrame(general_data)
    df_detailed = pd.DataFrame(detailed_data)
    
    # Definir orden de columnas
    common_columns = [
        'avg_success', 
        'max_success', 
        'min_success', 
        'avg_total_flips',  # Nueva columna
        'avg_time', 
        'phase_transition'
    ]
    
    # Reordenar columnas
    general_cols = ['Configuration'] + common_columns
    df_general = df_general[general_cols]
    
    detailed_cols = ['Configuration', 'n'] + common_columns
    df_detailed = df_detailed[detailed_cols]
    
    # Mostrar tablas en consola
    print("\nTabla General (Todos los n combinados):")
    print("="*120)
    print(tabulate(
        df_general, 
        headers='keys', 
        tablefmt='psql', 
        showindex=False, 
        floatfmt=".2f",
        colalign=("left",) + ("center",)*(len(common_columns))
    ))
    
    print("\nTabla Detallada (Desglose por n):")
    print("="*120)
    print(tabulate(
        df_detailed, 
        headers='keys', 
        tablefmt='psql', 
        showindex=False, 
        floatfmt=".2f",
        colalign=("left", "left") + ("center",)*(len(common_columns)))
    )
    
    # Guardar en diferentes formatos si se especifica un archivo de salida
    if output_file:
        base_name = output_file.replace('.txt', '')
        
        # Tabla general
        general_csv = f"{base_name}_general.csv".replace('\\metrics','\\metrics\\csv')
        df_general.to_csv(general_csv, index=False)
        print(f"\nTabla general guardada como CSV: {general_csv}")
        
        # general_tex = f"{base_name}_general.tex"
        # with open(general_tex, 'w') as f:
        #     f.write(df_general.to_latex(
        #         index=False, 
        #         float_format="%.2f",
        #         column_format="l" + "c"*len(common_columns)
        #     ))
        # print(f"Tabla general guardada como LaTeX: {general_tex}")
        
        general_md = f"{base_name}_general.md"
        with open(general_md, 'w') as f:
            f.write(df_general.to_markdown(
                index=False, 
                floatfmt=".2f",
                tablefmt="github"
            ))
        print(f"Tabla general guardada como Markdown: {general_md}")
        
        # Tabla detallada
        detailed_csv = f"{base_name}_detailed.csv".replace('\\metrics','\\metrics\\csv')
        df_detailed.to_csv(detailed_csv, index=False)
        print(f"Tabla detallada guardada como CSV: {detailed_csv}")
        
        # detailed_tex = f"{base_name}_detailed.tex"
        # with open(detailed_tex, 'w') as f:
        #     f.write(df_detailed.to_latex(
        #         index=False, 
        #         float_format="%.2f",
        #         column_format="ll" + "c"*(len(common_columns))
        #     ))
        # print(f"Tabla detallada guardada como LaTeX: {detailed_tex}")
        
        detailed_md = f"{base_name}_detailed.md"
        with open(detailed_md, 'w') as f:
            f.write(df_detailed.to_markdown(
                index=False, 
                floatfmt=".2f",
                tablefmt="github"
            ))
        print(f"Tabla detallada guardada como Markdown: {detailed_md}")
    
    return df_general, df_detailed


def generate_custom_grid(results_df, experiment_name, plot_file, 
                        vary_params, hue_param="n", fixed_params={'Max Tries': 3}, flips_coef=None,
                        metrics_output_file=None):
    """
    Genera una matriz de gráficos variando los parámetros especificados
    
    Args:
        vary_params: Lista de parámetros a variar (máximo 2 parámetros)
        fixed_params: Diccionario con parámetros fijos y sus valores
        metrics_output_file: Archivo para guardar las métricas comparativas
    """
    if results_df.empty:
        print("No hay datos para graficar.")
        return
    
    # Filtrar datos según parámetros fijos
    filtered_df = results_df.copy()
    if fixed_params:
        for param, value in fixed_params.items():
            if param in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[param] == value]
    
    # Convertir max_flips a coeficiente si se especifica
    if flips_coef:
        filtered_df = filtered_df[filtered_df['Max Flips'] == flips_coef * filtered_df['n']]

    # Verificar que hay parámetros para variar
    if not vary_params:
        print("Debes especificar al menos un parámetro para variar.")
        return
    
    # Limitar a 2 parámetros para variar (por claridad en la visualización)
    if len(vary_params) > 2:
        print("Advertencia: Solo se considerarán los primeros 2 parámetros para variar.")
        vary_params = vary_params[:2]
    
    # Obtener valores únicos para cada parámetro a variar
    param_values = {}
    for param in vary_params:
        if param != 'flips_coef':
            if param in filtered_df.columns:
                param_values[param] = sorted(filtered_df[param].unique())
            else:
                print(f"Advertencia: El parámetro '{param}' no existe en los datos.")
                return
        else:
            param_values[param] = [1,10,20,50]
    
    # Determinar dimensiones de la cuadrícula
    if len(vary_params) == 1:
        rows = 1
        cols = len(param_values[vary_params[0]])
    else:
        rows = len(param_values[vary_params[0]])
        cols = len(param_values[vary_params[1]])
    
    # Crear figura con subgráficos
    fig, axes = plt.subplots(
        nrows=rows,
        ncols=cols,
        figsize=(5*cols, 4*rows),
        squeeze=False
    )
    fig.suptitle(experiment_name, fontsize=12, y=1.02)
    
    # Diccionario para almacenar todas las métricas
    all_metrics = {}
    
    # Generar cada subgráfico
    if len(vary_params) == 1:
        # Caso con un solo parámetro para variar
        param = vary_params[0]
        for j, val in enumerate(param_values[param]):
            ax = axes[0, j]
                                                
            if 'flips_coef' not in vary_params:
                # Filtrar datos para este valor del parámetro
                group = filtered_df[filtered_df[param] == val]
            else:
                # Filtrar datos para este valor del parámetro y coeficiente de flips
                group = filtered_df[(filtered_df['Max Flips'] == val * filtered_df['n'])]
            
            if not group.empty:
                fixed = {**fixed_params, param: val}
                metrics, config_name = generate_subplot(ax, group, hue_param, None, fixed)
                all_metrics[config_name] = metrics
            else:
                ax.axis('off')
    else:
        # Caso con dos parámetros para variar
        param1, param2 = vary_params
        for i, val1 in enumerate(param_values[param1]):
            for j, val2 in enumerate(param_values[param2]):
                ax = axes[i, j]
                
                if 'flips_coef' not in vary_params:
                    # Filtrar datos para esta combinación de parámetros
                    group = filtered_df[(filtered_df[param1] == val1) & 
                                        (filtered_df[param2] == val2)]
                elif 'flips_coef' == param1:
                    # Filtrar datos para esta combinación de parámetros y coeficiente de flips
                    group = filtered_df[(filtered_df[param1] == val2) & 
                                        (filtered_df['Max Flips'] == val1 * filtered_df['n'])]
                else:
                    group = filtered_df[(filtered_df[param1] == val1) & 
                                        (filtered_df['Max Flips'] == val2 * filtered_df['n'])]
                
                if not group.empty:
                    fixed = {**fixed_params, param1: val1, param2: val2}
                    metrics, config_name = generate_subplot(ax, group, hue_param, None, fixed)
                    all_metrics[config_name] = metrics
                else:
                    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nGràfico guardado en: {plot_file}")
    
    # Generar y guardar tabla comparativa si se especificó
    if metrics_output_file and all_metrics:
        generate_metrics_tables(all_metrics, metrics_output_file)

def analyze_results(filename):
    """Función principal para analizar los resultados"""
    df = parse_results_file(filename)
      
    # Ejemplo con tabla comparativa
    # Construir nombres de archivos de salida a partir del nombre de entrada
    base_name = filename
    if base_name.lower().endswith('.txt'):
        base_name = base_name[:-4]
    plot_file = base_name.replace('results/', 'results\\plots\\') + '.png'
    metrics_output_file = base_name.replace('results/', 'results\\metrics\\') + '.txt'

    generate_custom_grid(
        df,
        experiment_name="Success Rate by Community Size and Randomness",
        plot_file=plot_file,
        vary_params=['c', 'Q'],  # o flips_coef
        # vary_params=['max_tries', 'flips_coef'],
        fixed_params={'p': 0.5, 'max_tries': 3, 'flips_coef': 1},
        # fixed_params={'p':0.5, 'Q':0.8, 'c':10},
        metrics_output_file=metrics_output_file
    )

# Ejemplo de uso
if __name__ == "__main__":
    filename = r"results/results_WalkSAT_community_v02_1n.txt"
    analyze_results(filename)