import pandas as pd
import os
from tabulate import tabulate

def load_results(directory):
    """Carga todos los archivos CSV de resultados en un solo DataFrame"""
    all_data = []
    
    for filename in os.listdir(directory):
        if filename.endswith("_general.csv"):
            algorithm = filename.replace("_general.csv", "")
            df = pd.read_csv(os.path.join(directory, filename))
            df['Algorithm'] = algorithm
            all_data.append(df)
    
    if not all_data:
        raise ValueError("No se encontraron archivos de resultados en el directorio especificado")
    
    return pd.concat(all_data, ignore_index=True)

def normalize_scores(df):
    """Normaliza las métricas para comparación (mayor es mejor)"""
    # Invertir tiempo (queremos menor tiempo)
    df['norm_time'] = 1 / (1 + df['avg_time'])
    
    # Normalizar otras métricas (ya que mayor es mejor)
    for col in ['avg_success', 'max_success', 'phase_transition']:
        if col in df.columns:
            df[f'norm_{col}'] = df[col] / df[col].max()
    
    return df

def calculate_composite_score(df, weights):
    """Calcula una puntuación compuesta basada en pesos"""
    score_components = []
    
    if 'norm_avg_success' in df.columns and 'avg_success' in weights:
        score_components.append(df['norm_avg_success'] * weights['avg_success'])
    
    if 'norm_max_success' in df.columns and 'max_success' in weights:
        score_components.append(df['norm_max_success'] * weights['max_success'])
    
    if 'norm_phase_transition' in df.columns and 'phase_transition' in weights:
        score_components.append(df['norm_phase_transition'] * weights['phase_transition'])
    
    if 'norm_time' in df.columns and 'avg_time' in weights:
        score_components.append(df['norm_time'] * weights['avg_time'])
    
    if not score_components:
        raise ValueError("No hay métricas válidas para calcular la puntuación")
    
    df['Composite_Score'] = sum(score_components)
    return df

def compare_algorithms(results_dir, output_file=None, weights=None):
    """
    Compara el desempeño de diferentes algoritmos y determina el mejor
    
    Args:
        results_dir: Directorio con los archivos CSV de resultados
        output_file: Archivo para guardar los resultados de comparación
        weights: Diccionario con pesos para cada métrica (ej: {'avg_success': 0.4, 'avg_time': 0.3})
                 Si es None, usa pesos por defecto
    """
    if weights is None:
        weights = {
            'avg_success': 0.4,
            'max_success': 0.2,
            'phase_transition': 0.2,
            'avg_time': 0.2
        }
    
    try:
        # Cargar y preparar datos
        df = load_results(results_dir)
        df = normalize_scores(df)
        df = calculate_composite_score(df, weights)
        
        # Agrupar por algoritmo y calcular métricas agregadas
        comparison_df = df.groupby('Algorithm').agg({
            'avg_success': 'mean',
            'max_success': 'mean',
            'avg_time': 'mean',
            'phase_transition': 'mean',
            'Composite_Score': 'mean'
        }).sort_values('Composite_Score', ascending=False)
        
        # Formatear para mejor visualización
        comparison_df = comparison_df.reset_index()
        comparison_df['Rank'] = range(1, len(comparison_df) + 1)
        
        # Reordenar columnas
        cols = ['Rank', 'Algorithm', 'Composite_Score', 'avg_success', 'max_success', 
                'phase_transition', 'avg_time']
        comparison_df = comparison_df[[c for c in cols if c in comparison_df.columns]]
        
        # Mostrar resultados
        print("\nComparación de Algoritmos:")
        print("="*90)
        print(tabulate(comparison_df, headers='keys', tablefmt='psql', showindex=False, floatfmt=".2f"))
        
        # Determinar el mejor algoritmo
        best_algo = comparison_df.iloc[0]['Algorithm']
        best_score = comparison_df.iloc[0]['Composite_Score']
        print(f"\nMEJOR ALGORITMO: {best_algo} (Puntuación: {best_score:.2f})")
        
        # Guardar resultados si se especifica
        if output_file:
            # # CSV
            # csv_file = output_file.replace('.txt', '.csv')
            # comparison_df.to_csv(csv_file, index=False)
            # print(f"\nResultados guardados como CSV: {csv_file}")
            
            # # LaTeX
            # latex_file = output_file.replace('.txt', '.tex')
            # with open(latex_file, 'w') as f:
            #     f.write(comparison_df.to_latex(index=False, float_format=".2f"))
            # print(f"Resultados guardados como LaTeX: {latex_file}")
            
            # Markdown
            md_file = output_file.replace('.txt', '.md')
            with open(md_file, 'w') as f:
                f.write(comparison_df.to_markdown(index=False, floatfmt=".2f"))
            print(f"Resultados guardados como Markdown: {md_file}")
        
        return comparison_df
    
    except Exception as e:
        print(f"\nError al comparar algoritmos: {str(e)}")
        return None

# Ejemplo de uso
if __name__ == "__main__":
    # Configuración
    results_directory = r"results/metrics/csv"  # Directorio con los CSV de resultados
    output_comparison = results_directory + r"/comparacion_algoritmos.txt"
    
    # Pesos personalizados (opcional)
    custom_weights = {
        'avg_success': 0.5,   # Mayor peso a la tasa de éxito promedio
        'max_success': 0.1,
        'phase_transition': 0.2,
        'avg_time': 0.2
    }
    
    # Comparar algoritmos
    comparison_results = compare_algorithms(
        results_dir=results_directory,
        output_file=output_comparison,
        weights=custom_weights  # Usar None para pesos por defecto
    )