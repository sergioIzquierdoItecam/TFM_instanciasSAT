# -*- coding: utf-8 -*-
"""
Módulo completo para ejecutar experimentos con WalkSAT
"""

import os
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from WalkSAT_v01 import WalkSAT
from datetime import datetime
import re
from tqdm import tqdm  # Para barras de progreso

def load_existing_results(results_file):
    """Carga todos los resultados existentes del archivo TXT de forma robusta"""
    data = []
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or 'Success:' not in line:
                    continue
                
                # Extracción robusta de parámetros usando expresiones regulares
                config_pattern = r'c=([\d.]+),\s*Q=([\d.]+),\s*p=([\d.]+),\s*n=([\d.]+),\s*m/n=([\d.]+)'
                match = re.search(config_pattern, line)
                if not match:
                    continue
                
                c, Q, p, n, m_n = map(float, match.groups())
                
                # Extracción de resultados
                success = float(re.search(r'Success:\s*([\d.]+)%', line).group(1))
                flips = int(re.search(r'Total Flips:\s*(\d+)', line).group(1))
                time_sec = float(re.search(r'Time:\s*([\d.]+)\s*seconds', line).group(1)) if 'Time:' in line else 0.0
                
                data.append({
                    'Configurations': f"c={int(c)}, Q={Q:.1f}, p={p:.1f}, n={int(n)}, m/n={float(m_n):.1f}",
                    'WalkSAT Success': success,
                    'Time (seconds)': time_sec,
                    'Total Flips': flips,
                    'c': int(c),
                    'Q': float(Q),
                    'p': float(p),
                    'n': int(n),
                    'm/n': float(m_n)
                })
    
    return pd.DataFrame(data) if data else None

def run_single_configuration(config_params, num_seeds=100):
    """Ejecuta una configuración específica con múltiples semillas"""
    results = {
        'success_count': 0,
        'total_flips': 0,
        'start_time': time.time()
    }
    
    # Preparar parámetros fijos para WalkSAT
    fixed_params = {
        'num_vars': config_params['n'],
        'num_clauses': int(config_params['m_n'] * config_params['n']),
        'k': config_params['k'],
        'Q': config_params['Q'],
        'c': config_params['c'],
        'max_flips': config_params['max_flips'],
        'max_tries': config_params['max_tries'],
        'p': config_params['p']
    }
    
    # Ejecutar para cada semilla
    seeds = random.sample(range(1001), num_seeds)
    for seed in seeds:
        solver = WalkSAT(
            variables=fixed_params['num_vars'],
            clauses=fixed_params['num_clauses'],
            clauseLength=fixed_params['k'],
            seed=seed,
            modularity=fixed_params['Q'],
            communities=fixed_params['c']
        )
        
        success, tries, flips = solver.solve(
            max_flips=fixed_params['max_flips'],
            max_tries=fixed_params['max_tries'],
            probability=fixed_params['p']
        )
        
        if success:
            results['success_count'] += 1
        results['total_flips'] += flips * tries
    
    # Calcular métricas finales
    results['success_rate'] = (results['success_count'] / num_seeds) * 100
    results['execution_time'] = time.time() - results['start_time']
    
    return results

def run_experiment(
    experiment_name,
    n_values,
    p_values,
    c_values,
    Q_values,
    k=3,
    max_tries=3,
    max_flips_coef=10,
    m_n_ratios=np.arange(2.5, 5.5, 0.1),
    num_seeds=100
):
    """Función principal para ejecutar un experimento completo con gestión de resultados"""
    
    # Preparar estructura de directorios
    os.makedirs('results', exist_ok=True)
    os.makedirs('plots', exist_ok=True)
    
    # Archivos de resultados
    results_txt_file = f'results/results_{experiment_name}.txt'
    results_excel_file = f'results/results_{experiment_name}.xlsx'
    plot_file = f'plots/performance_{experiment_name}.png'
    
    # Cargar resultados existentes
    results_df = load_existing_results(results_txt_file)
    if results_df is None:
        results_df = pd.DataFrame(columns=[
            'Configurations', 'WalkSAT Success', 'Time (seconds)', 
            'Total Flips', 'c', 'Q', 'p', 'n', 'm/n'
        ])
    
    # Convertir a conjunto para búsquedas rápidas
    completed_configs = set(results_df['Configurations'].unique()) if not results_df.empty else set()
    
    # Registrar metadatos del experimento
    with open(results_txt_file, 'a' if os.path.exists(results_txt_file) else 'w') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Experiment: {experiment_name}\n")
        f.write(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Parameters:\n")
        f.write(f"  n_values: {n_values}\n")
        f.write(f"  p_values: {p_values}\n")
        f.write(f"  c_values: {c_values}\n")
        f.write(f"  Q_values: {Q_values}\n")
        f.write(f"  k: {k}\n")
        f.write(f"  max_tries: {max_tries}\n")
        f.write(f"  max_flips_coef: {max_flips_coef}\n")
        f.write(f"  m_n_ratios: {list(m_n_ratios)}\n")
        f.write(f"{'='*80}\n\n")
    
    # Progreso total estimado
    total_combinations = len(n_values) * len(p_values) * len(c_values) * len(Q_values) * len(m_n_ratios)
    pbar = tqdm(total=total_combinations, desc="Overall Progress")
    
    try:
        # Iterar sobre todas las combinaciones de parámetros
        for n in n_values:
            max_flips = max_flips_coef * n
            
            for p in p_values:
                for c in c_values:
                    for Q in Q_values:
                        consecutive_failures = 0
                        
                        for m_n in m_n_ratios:
                            config_str = f'c={c}, Q={Q}, p={p}, n={n}, m/n={m_n:.1f}'
                            pbar.set_postfix_str(config_str)
                            
                            # Saltar configuraciones ya completadas
                            if config_str in completed_configs:
                                pbar.update(1)
                                continue
                            
                            # Ejecutar configuración
                            config_params = {
                                'n': n,
                                'p': p,
                                'c': c,
                                'Q': Q,
                                'k': k,
                                'max_tries': max_tries,
                                'max_flips': max_flips,
                                'm_n': m_n
                            }
                            
                            results = run_single_configuration(config_params, num_seeds)
                            
                            # Manejar fracasos consecutivos
                            if results['success_rate'] == 0:
                                consecutive_failures += 1
                                if consecutive_failures >= 3:
                                    # Saltar ratios restantes si hay muchos fracasos
                                    remaining = len(m_n_ratios) - (np.where(m_n_ratios == m_n)[0][0] + 1)
                                    pbar.update(remaining + 1)
                                    break
                            else:
                                consecutive_failures = 0
                            
                            # Registrar resultados
                            new_row = {
                                'Configurations': config_str,
                                'WalkSAT Success': results['success_rate'],
                                'Time (seconds)': results['execution_time'],
                                'Total Flips': results['total_flips'],
                                'c': c,
                                'Q': Q,
                                'p': p,
                                'n': n,
                                'm/n': m_n
                            }
                            
                            results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
                            completed_configs.add(config_str)
                            
                            # Guardar incrementalmente
                            with open(results_txt_file, 'a') as f:
                                f.write(f"{config_str}, WalkSAT Success: {results['success_rate']:.1f}%, "
                                      f"Total Flips: {results['total_flips']}, "
                                      f"Time: {results['execution_time']:.2f} seconds\n")
                            
                            results_df.to_excel(results_excel_file, index=False)
                            pbar.update(1)
    
    finally:
        pbar.close()
        generate_plots(results_df, experiment_name, plot_file)
    
    return results_df

def generate_plots(results_df, experiment_name, plot_file):
    """Genera gráficos completos con estilo profesional"""
    if results_df.empty:
        print("No hay datos para graficar")
        return
    
    plt.style.use('seaborn-v0_8')
    plt.figure(figsize=(14, 8))
    
    # Agrupar por parámetros clave (excluyendo m/n)
    group_cols = ['c', 'Q', 'p', 'n']
    grouped = results_df.groupby(group_cols)
    
    # Configuración de colores y estilos
    colors = plt.cm.tab20(np.linspace(0, 1, len(grouped)))
    markers = ['o', 's', '^', 'v', '>', '<', 'p', '*', 'h', 'H', 'D', 'd']
    
    for (key, group), color, marker in zip(grouped, colors, markers):
        label = (f"c={key[0]}, Q={key[1]:.1f}, p={key[2]:.1f}, " 
                f"n={key[3]}, flips={10*key[3] if len(key) <5 else key[4]}")
        
        # Ordenar por ratio m/n
        group = group.sort_values('m/n')
        
        plt.plot(group['m/n'], group['WalkSAT Success'], 
                label=label, color=color, marker=marker, 
                linestyle='--', linewidth=1.5, markersize=8)
    
    plt.title(f"Performance de WalkSAT\n{experiment_name}", pad=20)
    plt.xlabel("Ratio de Cláusulas/Variables (m/n)", labelpad=15)
    plt.ylabel("Tasa de Éxito (%)", labelpad=15)
    plt.ylim(-5, 105)
    plt.grid(True, alpha=0.3)
    
    # Leyenda fuera del gráfico
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              borderaxespad=0., frameon=True, 
              title="Configuraciones:")
    
    # Ajustes de diseño
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico guardado en {plot_file}")

if __name__ == "__main__":
    # Ejemplo de uso directo (para testing)
    test_results = run_experiment(
        experiment_name="test_run",
        n_values=[20, 50],
        p_values=[0.3, 0.5],
        c_values=[5],
        Q_values=[0.2],
        m_n_ratios=np.arange(2.5, 3.6, 0.5),
        num_seeds=10  # Reducido para prueba
    )