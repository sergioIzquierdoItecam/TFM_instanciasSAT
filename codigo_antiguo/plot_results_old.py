import matplotlib.pyplot as plt
import pandas as pd
import re
from itertools import cycle
from collections import defaultdict

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
            elif line.startswith('c='):
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
                            entry['Max Flips'] = float(value)

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

def generate_comparison_plots(results_df, experiment_name, plot_file, hue_param="n", 
                            fixed_params={'c': 10, 'Max Tries': 3}, flips_coef=None):
    """
    Genera gráficos comparativos con estilo similar al ejemplo proporcionado
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

    # Configuración del gráfico
    plt.figure(figsize=(10, 6))
    colors = cycle(plt.cm.tab10.colors)
    markers = cycle(['o', 's', '^', 'D', 'v', 'p', '*', 'h', '8', 'X'])

    # Agrupar por el parámetro de diferenciación (hue_param)
    grouped = filtered_df.groupby(hue_param)
    
    # Diccionario para almacenar métricas cuantitativas
    metrics = defaultdict(dict)
    
    for (hue_value, group), color, marker in zip(grouped, colors, markers):
        group = group.sort_values('m/n')
        
        # Calcular métricas cuantitativas
        metrics[hue_value]['avg_success'] = group['Success Rate'].mean()
        metrics[hue_value]['max_success'] = group['Success Rate'].max()
        
        # Encontrar el punto de transición de fase (donde success rate < 50%)
        critical_points = group[group['Success Rate'] < 50]['m/n']
        if not critical_points.empty:
            metrics[hue_value]['phase_transition'] = critical_points.min()
        
        # Graficar
        plt.plot(
            group['m/n'], 
            group['Success Rate'], 
            label=f"{hue_param}={hue_value}",
            color=color,
            marker=marker,
            linestyle='--',
            linewidth=2,
            markersize=8
        )

    # Configuración del gráfico
    title = f"Success Rate Comparison - {experiment_name}"
    if fixed_params:
        fixed_str = ", ".join(f"{k}={v}" for k, v in fixed_params.items())
        title += f"\n(Fixed: {fixed_str}"
        if flips_coef:
            title += f", max_flips={flips_coef}n"
        title += ")"
    
    plt.title(title, fontsize=12, pad=20)
    plt.xlabel("Ratio of Clauses to Variables (m/n)", fontsize=10)
    plt.ylabel("Success Rate (%)", fontsize=10)
    plt.ylim(-5, 105)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Ajustes estéticos
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico guardado en: {plot_file}")
    
    # Mostrar métricas cuantitativas
    print("\nMétricas Cuantitativas:")
    print("----------------------")
    for param_value, param_metrics in metrics.items():
        print(f"\nConfiguración {hue_param}={param_value}:")
        print(f"  - Tasa de éxito promedio: {param_metrics['avg_success']:.1f}%")
        print(f"  - Máxima tasa de éxito: {param_metrics['max_success']:.1f}%")
        if 'phase_transition' in param_metrics:
            print(f"  - Transición de fase (m/n <50%): {param_metrics['phase_transition']:.2f}")

def analyze_results(filename):
    """Función principal para analizar los resultados"""
    df = parse_results_file(filename)
    
    # # Análisis 1: Comparar diferentes valores de Q (aleatoriedad)
    # generate_comparison_plots(
    #     df, 
    #     experiment_name="Effect of Randomness (Q)", 
    #     plot_file="success_rate_vs_mn_by_Q.png",
    #     hue_param="Q",
    #     fixed_params={'c': 10, 'Max Tries': 3}
    # )
    
    # # Análisis 2: Comparar diferentes tamaños de comunidad (c)
    # generate_comparison_plots(
    #     df, 
    #     experiment_name="Effect of Community Size (c)", 
    #     plot_file="success_rate_vs_mn_by_c.png",
    #     hue_param="c",
    #     fixed_params={'Q': 0.5, 'Max Tries': 3}
    # )
    
    # Análisis 3: Comparar diferentes tamaños de problema (n)
    generate_comparison_plots(
        df, 
        experiment_name="Effect of Problem Size (n)", 
        plot_file=r"plots/performance_WalkSAT_community_v00_02.png",
        hue_param="n",
        fixed_params={'max_tries': 1},
        flips_coef=10  # Usar coeficiente de max_flips
    )

# Ejemplo de uso
if __name__ == "__main__":
    filename = r"results/results_WalkSAT_community_v00_flips&tries.txt"
    analyze_results(filename)