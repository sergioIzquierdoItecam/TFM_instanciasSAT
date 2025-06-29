# -*- coding: utf-8 -*-
"""
Módulo mejorado para ejecutar experimentos con WalkSAT en paralelo
"""

import os
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from algorithms.WalkSAT import WalkSAT as WalkSAT_random
from algorithms.WalkSAT_v00 import WalkSAT as WalkSAT_community_v00
from algorithms.WalkSAT_v01 import WalkSAT as WalkSAT_community_v01
from algorithms.WalkSAT_v02 import WalkSAT as WalkSAT_community_v02
from algorithms.WalkSAT_v03 import WalkSAT as WalkSAT_community_v03
from algorithms.WalkSAT_v04 import WalkSAT as WalkSAT_community_v04
from algorithms.WalkSAT_vXX import WalkSAT as WalkSAT_community_vXX
from algorithms.GSAT import GSAT
from datetime import datetime
import re
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import warnings
warnings.filterwarnings('ignore')

# Configuración global
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 2)
CHUNK_SIZE = 10
MAX_RETRIES = 3  # Intentos máximos por configuración fallida

def run_single_configuration(config_params, num_seeds=100, algorithm_type='WalkSAT_community', experiment_name='WalkSAT_community'):
    """Ejecuta una configuración con reintentos automáticos"""
    for attempt in range(MAX_RETRIES):
        results = {
            'success_count': 0,
            'total_flips': 0,
            'start_time': time.time()
        }
        
        seeds = random.sample(range(1001), num_seeds)
        for seed in seeds:
            # seed = 2144  # Para pruebas, usar un seed fijo
            if algorithm_type == 'WalkSAT_community':
                # Seleccionar la versión de WalkSAT_community según el experiment_name
                if "v00" in experiment_name:
                    solver_class = WalkSAT_community_v00
                elif "v01" in experiment_name:
                    solver_class = WalkSAT_community_v01
                elif "v02" in experiment_name:
                    solver_class = WalkSAT_community_v02
                elif "v03" in experiment_name:
                    solver_class = WalkSAT_community_v03
                elif "v04" in experiment_name:
                    solver_class = WalkSAT_community_v04
                else:
                    solver_class = WalkSAT_community_vXX  # Por defecto, v00

                solver = solver_class(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed,
                    modularity=config_params['Q'],
                    communities=config_params['c']
                )
                success, tries, flips = solver.solve(
                max_flips=config_params['max_flips'],
                max_tries=config_params['max_tries'],
                probability=config_params['p'] if 'p' in config_params else None 
            )
            elif algorithm_type == 'WalkSAT_random':
                solver = WalkSAT_random(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed
                )
                success, tries, flips = solver.solve(
                max_flips=config_params['max_flips'],
                max_tries=config_params['max_tries'],
                probability=config_params['p'] if 'p' in config_params else None 
            )
            else:
                solver = GSAT(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed
                )
                success, tries, flips = solver.solve(
                    max_flips=config_params['max_flips'],
                    max_tries=config_params['max_tries'],
                )
            
            if success:
                results['success_count'] += 1
            results['total_flips'] += flips * tries
        
        results['success_rate'] = (results['success_count'] / num_seeds) * 100
        results['execution_time'] = time.time() - results['start_time']
        return results

def check_completion_status(results_df, n_values, p_values=None, c_values=None, Q_values=None, m_n_ratios=None, algorithm_type='WalkSAT_community'):
    """Verifica si todos los experimentos están completos"""
    if results_df.empty:
        return False, set()
    
    required_configs = set()
    for n in n_values:
        for p in p_values:
            if algorithm_type == 'WalkSAT_community':
                for c in c_values:
                    for Q in Q_values:
                        for m_n in m_n_ratios:
                            config_str = f'c={c}, Q={Q}, p={p}, n={n}, m/n={m_n:.1f}'
                            required_configs.add(config_str)
            elif algorithm_type == 'WalkSAT_random':
                for m_n in m_n_ratios:
                    config_str = f'p={p}, n={n}, m/n={m_n:.1f}'
                    required_configs.add(config_str)
            else:
                for m_n in m_n_ratios:
                    config_str = f'n={n}, m/n={m_n:.1f}'
                    required_configs.add(config_str)
    
    completed_configs = set(results_df['Configurations'].unique())
    missing_configs = required_configs - completed_configs
    
    return len(missing_configs) == 0, missing_configs

def analyze_failures(results_df):
    """Analiza resultados para detectar fracasos consecutivos"""
    failure_groups = {}
    
    if results_df.empty:
        return failure_groups
    
    results_df = results_df.sort_values(['n', 'm/n'])
    
    for n in results_df['n'].unique():
        group_df = results_df[results_df['n'] == n].sort_values('m/n')
        consecutive_fails = 0
        
        for _, row in group_df.iterrows():
            if row['Success Rate'] == 0:
                consecutive_fails += 1
                if consecutive_fails >= 2:
                    failure_groups[n] = row['m/n']
                    break
            else:
                consecutive_fails = 0
                
    return failure_groups

def load_existing_results(results_file):
    """Carga resultados existentes o retorna None si no existe el archivo"""
    if not os.path.exists(results_file):
        return None
    
    data = []
    with open(results_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or 'Success Rate:' not in line:
                continue
            
            try:
                parts = [p.strip() for p in line.split(',')]
                config_data = {}
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=')
                        config_data[key.strip()] = value.strip()
                    elif 'Success Rate:' in part:
                        config_data['Success'] = float(part.split(':')[1].strip('%'))
                    elif 'Total Flips:' in part:
                        config_data['Flips'] = int(part.split(':')[1].strip())
                    elif 'Time:' in part:
                        config_data['Time'] = float(part.split(':')[1].replace('seconds', '').strip())
                
                # Determinar el tipo de configuración
                if 'c' in config_data and 'Q' in config_data:
                    # Configuración con Q y c
                    data.append({
                        'Configurations': f"c={config_data['c']}, Q={config_data['Q']}, p={config_data['p']}, n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'c': int(config_data['c']),
                        'Q': float(config_data['Q']),
                        'p': float(config_data['p']),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
                elif 'p' in config_data:
                    # Configuración sin Q y c
                    data.append({
                        'Configurations': f"p={config_data['p']}, n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'p': float(config_data['p']),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
                else:
                    # Configuración sin c y Q
                    data.append({
                        'Configurations': f"n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
            except Exception as e:
                print(f"Error procesando línea: {line}\nError: {str(e)}")
                continue
    
    return pd.DataFrame(data) if data else None

def fill_automatic_configurations(all_configs,results_df, results_txt_file):
    """Rellena automáticamente configuraciones pendientes basadas en resultados anteriores"""
        # Paso 4: Si hay configuraciones pendientes, ejecutarlas

    try:
        i = 0
        while i < len(all_configs):
            current_config = all_configs[i]
            current_m_n = current_config['params']['m_n']
            
            if 'c' in current_config['params'] and 'Q' in current_config['params']:

                # Obtener todos los resultados para este n, ordenados por m/n
                current_n_results = results_df[(results_df['n'] == current_config['params']['n']) & 
                                (results_df['c'] == current_config['params']['c']) & 
                                (results_df['p'] == current_config['params']['p']) & 
                                (results_df['Q'] == current_config['params']['Q']) &
                                (results_df['Max Tries'] == current_config['params']['max_tries']) &
                                (results_df['Max Flips'] == current_config['params']['max_flips'])
                                ].sort_values('m/n')   
                
            elif 'p' in current_config['params']:
                # Obtener todos los resultados para este n, ordenados por m/n
                current_n_results = results_df[(results_df['n'] == current_config['params']['n']) & 
                                (results_df['p'] == current_config['params']['p']) &
                                (results_df['Max Tries'] == current_config['params']['max_tries']) &
                                (results_df['Max Flips'] == current_config['params']['max_flips'])
                                ].sort_values('m/n')
                
            else:
                # Obtener todos los resultados para este n, ordenados por m/n
                current_n_results = results_df[(results_df['n'] == current_config['params']['n'])&
                                (results_df['Max Tries'] == current_config['params']['max_tries']) &
                                (results_df['Max Flips'] == current_config['params']['max_flips'])].sort_values('m/n')
                
            # Encontrar los dos valores de m/n anteriores al actual
            previous_results = current_n_results[current_n_results['m/n'] < current_m_n]
            
            # Verificar si hay al menos dos resultados anteriores y ambos tienen éxito 0%
            if len(previous_results) >= 2:
                last_two = previous_results.tail(2)
                if all(last_two['Success Rate'] == 0):
                    # Rellenar automáticamente esta configuración con 0%
                    last_flips = last_two.iloc[-1]['Total Flips']
                                
                            
                    if 'c' in current_config['params'] and 'Q' in current_config['params']:

                        new_row = {
                            'Configurations': current_config['config_str'],
                            'Success Rate': 0.0,
                            'Time (seconds)': 0.0,
                            'Total Flips': last_flips,
                            'Max Tries': current_config['params']['max_tries'],
                            'Max Flips': current_config['params']['max_flips'],
                            'c': current_config['params']['c'],
                            'Q': current_config['params']['Q'],
                            'p': current_config['params']['p'],
                            'n': current_config['params']['n'],
                            'm/n': current_m_n
                        }

                    elif 'p' in current_config['params']:
                        new_row = {
                            'Configurations': current_config['config_str'],
                            'Success Rate': 0.0,
                            'Time (seconds)': 0.0,
                            'Total Flips': last_flips,
                            'Max Tries': current_config['params']['max_tries'],
                            'Max Flips': current_config['params']['max_flips'],
                            'p': current_config['params']['p'],
                            'n': current_config['params']['n'],
                            'm/n': current_m_n
                        }
                    else:
                        new_row = {
                            'Configurations': current_config['config_str'],
                            'Success Rate': 0.0,
                            'Time (seconds)': 0.0,
                            'Total Flips': last_flips,
                            'Max Tries': current_config['params']['max_tries'],
                            'Max Flips': current_config['params']['max_flips'],
                            'n': current_config['params']['n'],
                            'm/n': current_m_n
                        }
                    # Añadir al DataFrame
                    results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Actualizar archivo
                    with open(results_txt_file, 'a') as f:
                        f.write(f"{new_row['Configurations']}, Success Rate: 0.0%, "
                            f"Total Flips: {new_row['Total Flips']}, Time: 0.00 seconds\n")

                    # Actualizar la barra de progreso
                    # pbar.update(1)
                    
                    # Eliminar esta configuración de all_configs
                    all_configs.pop(i)
                    continue  # No incrementar i ya que hemos eliminado un elemento
                    
            # Si no se cumple la condición, procesar normalmente
            # (tu código original para ejecutar en chunks)
            # if i % CHUNK_SIZE == 0 and i > 0:
                # Guardar resultados parciales
                # results_df.to_csv(results_csv_file, index=False)
                
            i += 1
        
        return all_configs, results_df
    except Exception as e:
        print(f"Error: {e}")

def run_experiment_parallel(
    experiment_name,
    n_values,
    p_values=None,
    c_values=None,
    Q_values=None,
    k=3,
    max_tries_values=[3],
    max_flips_values=None,       # Lista de valores absolutos
    max_flips_coef_values=None,  # Lista de coeficientes
    m_n_ratios=np.arange(2.5, 5.5, 0.1),
    num_seeds=100,
    algorithm_type='WalkSAT_community'
):
    """Función principal que inicia experimentos si no existen resultados"""
    os.makedirs('results', exist_ok=True)
    # os.makedirs('plots', exist_ok=True)
    
    results_txt_file = f'results/results_{experiment_name}.txt'
    results_excel_file = f'results/results_{experiment_name}.xlsx'
    plot_file = f'plots/performance_{experiment_name}.png'
    
    # Paso 1: Verificar si hay resultados existentes
    results_df = load_existing_results(results_txt_file)

    # Paso 2: Si no hay resultados, inicializar DataFrame vacío
    if results_df is None:
        print("\nNo se encontraron resultados previos. Iniciando experimentos desde cero...")
        results_df = pd.DataFrame(columns=[
            'Configurations', 'Success Rate', 'Time (seconds)', 
            'Total Flips', 'Max Tries', 'Max Flies','c', 'Q', 'p', 'n', 'm/n'
        ])
        
        # Escribir encabezado en archivo TXT
        with open(results_txt_file, 'w') as f:
            f.write(f"Experimento: {experiment_name}\n")
            f.write(f"Fecha de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
    else:
        print("\nResultados previos encontrados. Continuando desde el último punto...")
    
    # Paso 3: Generar todas las configuraciones posibles
    all_configs = []
    for n in n_values:
        for max_tries in max_tries_values:
            # Determinar los valores de max_flips a usar
            if max_flips_values is not None:
                # Usar valores absolutos directamente
                current_max_flips_list = max_flips_values
            else:
                # Calcular max_flips como coeficiente * n
                current_max_flips_list = [coef * n for coef in max_flips_coef_values]
            
            for max_flips in current_max_flips_list:
                if algorithm_type != 'GSAT':
                    for p in p_values:
                        if algorithm_type == 'WalkSAT_community':
                            for c in c_values:
                                for Q in Q_values:
                                    for m_n in m_n_ratios:
                                        config_str = f'c={c}, Q={Q}, p={p}, n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                                        # Verificar si la configuración ya existe
                                        if not results_df.empty and config_str in results_df['Configurations'].values:
                                            continue
                                        # Evita errores procedentes del generador de clásulas
                                        if n == 50 and c in [20,30]:
                                            continue
                                        all_configs.append({
                                            'config_str': config_str,
                                            'params': {
                                                'n': n,
                                                'p': p,
                                                'c': c,
                                                'Q': Q,
                                                'k': k,
                                                'max_tries': max_tries,
                                                'max_flips': max_flips,
                                                'm_n': m_n
                                            }
                                        })
                        else:
                            for m_n in m_n_ratios:
                                config_str = f'p={p}, n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                                if not results_df.empty and config_str in results_df['Configurations'].values:
                                            continue
                                all_configs.append({
                                    'config_str': config_str,
                                    'params': {
                                        'n': n,
                                        'p': p,
                                        'k': k,
                                        'max_tries': max_tries,
                                        'max_flips': max_flips,
                                        'm_n': m_n
                                    }
                                })
                else:
                    for m_n in m_n_ratios:
                        config_str = f'n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                        if not results_df.empty and config_str in results_df['Configurations'].values:
                            continue
                                          
                        all_configs.append({
                            'config_str': config_str,
                            'params': {
                                'n': n,
                                'k': k,
                                'max_tries': max_tries,
                                'max_flips': max_flips,
                                'm_n': m_n
                            }
                        })
    

    if all_configs:
        print(f"\nEjecutando {len(all_configs)} configuraciones pendientes...")
        pbar = tqdm(total=len(all_configs), desc="Progreso")
        if not results_df.empty:
            all_configs, results_df = fill_automatic_configurations(all_configs, results_df, results_txt_file)
        try:    
            i = 0
            while( i < len(all_configs)):
                chunk = all_configs[i:i + CHUNK_SIZE]
                i+= len(chunk)
                if not results_df.empty:
                    chunk, results_df = fill_automatic_configurations(chunk, results_df, results_txt_file)
                pbar.update(CHUNK_SIZE-len(chunk))
                
                with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {
                        executor.submit(run_single_configuration, config['params'], num_seeds, algorithm_type, experiment_name): config
                        for config in chunk
                    }
                    
                    for future in as_completed(futures):
                        config = futures[future]
                        
                        try:
                            results = future.result()
                            if algorithm_type == 'WalkSAT_community':
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'c': config['params']['c'],
                                    'Q': config['params']['Q'],
                                    'p': config['params']['p'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            elif algorithm_type == 'WalkSAT_random':
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'p': config['params']['p'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            else:
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
                            
                            with open(results_txt_file, 'a') as f:
                                if 'p' in new_row:
                                    f.write(f"{config['config_str']}, Success Rate: {results['success_rate']:.1f}%, "
                                        f"Total Flips: {results['total_flips']}, "
                                        f"Time: {results['execution_time']:.2f} seconds\n")
                                else:
                                    f.write(f"{config['config_str']}, Success Rate: {results['success_rate']:.1f}%, "
                                        f"Total Flips: {results['total_flips']}, "
                                        f"Time: {results['execution_time']:.2f} seconds\n")
                            

                            
                        except Exception as e:
                            print(f"\nError en {config['config_str']}: {str(e)}")
                        
                        pbar.update(1)
                
                # Guardar progreso periódicamente
                # results_df.to_excel(results_excel_file, index=False)
        
        finally:
            pbar.close()
    else:
        print("\nNo hay configuraciones pendientes. Todos los experimentos están completos.")
    
    print("Ordenando resultados en los archivos...")
    clean_and_reorder_results(results_txt_file, results_df)
    # results_df.to_excel(results_excel_file, index=False)

    # Generar gráficos finales
    # generate_plots(results_df, experiment_name, plot_file)
    return results_df

import pandas as pd
from datetime import datetime

def clean_and_reorder_results(results_file, results_df):
    """Reordena y limpia el archivo de resultados, agrupando por parámetros con múltiples valores.
    
    Args:
        results_file (str): Ruta del archivo de resultados.
        results_df (pd.DataFrame): DataFrame con los resultados.
    """
    if 'c' in results_df and 'Q' in results_df:
        # Parámetros a considerar para agrupación (c, Q, p, n, m/n)
        group_params = ['n', 'c', 'Q', 'p', 'Max Tries', 'Max Flips']
    elif 'p' in results_df:
        # Parámetros a considerar para agrupación (p, n, m/n)
        group_params = ['n', 'p', 'Max Tries', 'Max Flips']
    else:
        # Parámetros a considerar para agrupación (n, m/n)
        group_params = ['n', 'Max Tries', 'Max Flips']
    
    # Identificar qué parámetros tienen más de un valor único (para agrupar)
    varying_params = [param for param in group_params 
                      if len(results_df[param].unique()) > 1]
    
    varying_params.append('m/n')  # Siempre incluir 'm/n' para ordenación
    # Si no hay parámetros variables, ordenar solo por 'm/n'
    if not varying_params:
        varying_params = ['m/n']
    
    # Ordenar el DataFrame por los parámetros variables (jerárquicamente)
    results_df = results_df.sort_values(varying_params)
    
    # Función auxiliar para escribir grupos recursivamente
    def write_groups(df, params, file_handle, indent_level=0):
        current_param = params[0] if params else None
        
        # Caso base: no hay más parámetros, escribir filas
        if not params:
            for _, row in df.iterrows():
                file_handle.write("    " * indent_level + 
                                f"{row['Configurations']}, Success Rate: {row['Success Rate']:.1f}%, "
                                f"Total Flips: {row['Total Flips']}, Time: {row['Time (seconds)']:.2f} seconds\n")
            return
        
        # Agrupar por el parámetro actual
        grouped = df.groupby(current_param, sort=False)
        
        for value, group in grouped:
            if current_param != 'm/n':
                file_handle.write("    " * indent_level + f"\n{'#' * 20} {current_param} = {value} {'#' * 20}\n")
                indent_level = -1
            write_groups(group, params[1:], file_handle, indent_level + 1)
    
    # Escribir el archivo de resultados
    with open(results_file, 'w') as f:
        f.write(f"Resultados ordenados - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")
        
        write_groups(results_df, varying_params, f)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Fin de resultados\n")

# import matplotlib.pyplot as plt
# from itertools import cycle

# def generate_faceted_plots(results_df, experiment_name, plot_file, 
#                           param1="n", param2="Q", fixed_params=None):
#     """
#     Genera un gráfico con subgráficos (facets) para cada valor de `param2`,
#     y dentro de cada subgráfico, las curvas se diferencian por `param1`.

#     Args:
#         results_df (pd.DataFrame): Datos de resultados.
#         experiment_name (str): Título general del gráfico.
#         plot_file (str): Ruta para guardar el gráfico.
#         param1 (str): Parámetro para diferenciar curvas (color/marcador).
#         param2 (str): Parámetro para crear subgráficos (facets).
#         fixed_params (dict): Parámetros fijos (ej: {"p": 0.5}).
#     """
#     if results_df.empty:
#         print("No hay datos para graficar.")
#         return

#     # Filtrar datos si hay parámetros fijos
#     if fixed_params:
#         filtered_df = results_df.copy()
#         for param, value in fixed_params.items():
#             filtered_df = filtered_df[filtered_df[param] == value]
#     else:
#         filtered_df = results_df

#     # Valores únicos de param2 (para número de subgráficos)
#     param2_values = filtered_df[param2].unique()
#     n_subplots = len(param2_values)

#     # Configurar figura y ejes
#     fig, axes = plt.subplots(1, n_subplots, figsize=(5 * n_subplots, 5), sharey=True)
#     if n_subplots == 1:
#         axes = [axes]  # Para evitar errores si solo hay un subgráfico

#     fig.suptitle(f"{experiment_name}\nDiferenciado por: {param1} | Subgráficos por: {param2}", y=1.05)
#     colors = cycle(plt.cm.tab10.colors)
#     markers = cycle(['o', 's', '^', 'D', 'v', 'p'])

#     # Iterar sobre cada valor de param2 (un subgráfico por valor)
#     for ax, param2_value in zip(axes, param2_values):
#         # Filtrar datos para el valor actual de param2
#         subset = filtered_df[filtered_df[param2] == param2_value]
        
#         # Agrupar por param1 y trazar curvas
#         grouped = subset.groupby(param1)
#         for (param1_value, group), color, marker in zip(grouped, colors, markers):
#             group = group.sort_values('m/n')
#             ax.plot(
#                 group['m/n'], 
#                 group['Success Rate'], 
#                 label=f"{param1}={param1_value}",
#                 color=color,
#                 marker=marker,
#                 linestyle='--'
#             )
        
#         ax.set_title(f"{param2} = {param2_value}")
#         ax.set_xlabel("Ratio of Clauses to Variables (m/n)")
#         ax.set_ylabel("Percentage of Solved Instances (%)" if ax == axes[0] else "")
#         ax.grid(True)
#         ax.legend()

#     plt.tight_layout()
#     plt.savefig(plot_file, dpi=300, bbox_inches='tight')
#     plt.close()
#     print(f"Gráfico guardado en: {plot_file}")

# from itertools import cycle

# import matplotlib.pyplot as plt
# from itertools import cycle

# def generate_plots(results_df, experiment_name, plot_file, hue_param="n", 
#                    fixed_params={'Max Tries': 50, 'Max Flips':1000}, flips_coef=None):
#     """
#     Genera gráficos diferenciando por `hue_param` y fijando `fixed_params`.
#     """
#     if results_df.empty:
#         print("No hay datos para graficar.")
#         return

#     # Filtrar datos según fixed_params (si se especifican)
#     if fixed_params:
#         filtered_df = results_df.copy()
#         for param, value in fixed_params.items():
#             filtered_df = filtered_df[filtered_df[param] == value]
#     else:
#         filtered_df = results_df

#     # Convertir max_flips a coeficiente si se solicita
#     if flips_coef:
#         filtered_df = filtered_df[filtered_df['Max Flips'] == flips_coef * filtered_df['n'] ]
#     # else:
#     #     hue_values = filtered_df[hue_param]

#     plt.figure(figsize=(10, 6))
#     colors = cycle(plt.cm.tab10.colors)
#     markers = cycle(['o', 's', '^', 'D', 'v', 'p'])

#     # Agrupar por hue_param
#     grouped = filtered_df.groupby(hue_param)
    
#     for (hue_value, group), color, marker in zip(grouped, colors, markers):
#         group = group.sort_values('m/n')
        
#         plt.plot(
#             group['m/n'], 
#             group['Success Rate'], 
#             label=f"{hue_param}={hue_value}",
#             color=color,
#             marker=marker,
#             linestyle='--'
#         )

#     # Título descriptivo
#     title = experiment_name
#     if fixed_params:
#         fixed_str = ", ".join(f"{k}={v}" for k, v in fixed_params.items())
#         title += f"\n(Fixed: {fixed_str})"
    
#     plt.title(title)
#     plt.xlabel("Ratio of Clauses to Variables (m/n)")
#     plt.ylabel("Percentage of Solved Instances (%)")
#     plt.ylim(-5, 105)
#     plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
#     plt.grid(True)
    
#     plt.tight_layout()
#     plt.savefig(plot_file, dpi=300, bbox_inches='tight')
#     plt.close()
#     print(f"Gráfico guardado en: {plot_file}")