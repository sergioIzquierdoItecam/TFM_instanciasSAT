# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 20:40:59 2024

@author: Sergio
"""

import time
import random
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
from WalkSAT_v01 import WalkSAT
from datetime import datetime
import os
import re

def load_existing_results(results_file):
    """Carga todos los resultados existentes del archivo TXT"""
    data = []
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ', WalkSAT Success:' in line:
                    # Extraer los parámetros y resultados
                    parts = [p.strip() for p in line.split(',')]
                    
                    config_data = {}
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=')
                            config_data[key.strip()] = value.strip()
                        elif 'Success:' in part:
                            config_data['Success'] = float(part.split(':')[1].split('%')[0].strip())
                        elif 'Total Flips:' in part:
                            config_data['Total Flips'] = int(part.split(':')[1].strip())
                        elif 'Time:' in part:
                            config_data['Time'] = float(part.split(':')[1].replace('seconds', '').strip())
                    
                    if all(k in config_data for k in ['c', 'Q', 'p', 'n', 'm/n', 'Success']):
                        data.append({
                            'Configurations': f"c={config_data['c']}, Q={config_data['Q']}, p={config_data['p']}, n={config_data['n']}, m/n={config_data['m/n']}",
                            'WalkSAT Success': config_data['Success'],
                            'Total Flips': config_data.get('Total Flips', 0),
                            'Time (seconds)': config_data.get('Time', 0),
                            'c': int(config_data['c']),
                            'Q': float(config_data['Q']),
                            'p': float(config_data['p']),
                            'n': int(config_data['n']),
                            'm/n': float(config_data['m/n'])
                        })
    
    return pd.DataFrame(data) if data else None

def run_experiment():
    # Nombre del archivo de resultados
    results_txt_file = f'results/results_{experiment_name}.txt'
    results_excel_file = f"results/results_{experiment_name}.xlsx"
    
    # Cargar resultados existentes
    existing_results = load_existing_results(results_txt_file)
    
    # Si hay resultados existentes, crear DataFrame con ellos
    if existing_results is not None:
        results_df = existing_results
        completed_configs = set(existing_results['Configurations'])
    else:
        results_df = pd.DataFrame(columns=['Configurations', 'WalkSAT Success', 'Time (seconds)', 'Total Flips', 'c', 'Q', 'p', 'n', 'm/n'])
        completed_configs = set()
    
    # Si el archivo de resultados no existe, crear el directorio si es necesario
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # Loop over each variable count in n
    for index_num_vars, num_vars in enumerate(n):
        # Calculate the number of clauses based on num_vars and a base ratio array m
        m = (m_n * num_vars).astype(int)
        
        # Variable to track consecutive zero success rates
        consecutive_zero_success = 0
        
        # Loop over each clause count in m
        for index_num_clauses, num_clauses in enumerate(m):
            config = f'c={c[index_num_vars]}, Q={Q[index_num_vars]}, p={p[index_num_vars]}, n={num_vars}, m/n={m_n[index_num_clauses]:.1f}'
            
            # Verificar si esta configuración ya fue completada
            if config in completed_configs:
                print(f"Configuración ya completada: {config}. Saltando...")
                continue
            
            print(f"Procesando configuración: {config}")
            
            if consecutive_zero_success >= 2:
                new_row = {
                    'Configurations': config,
                    'WalkSAT Success': 0,
                    'Time (seconds)': 0,
                    'Total Flips': 0,
                    'c': c[index_num_vars],
                    'Q': Q[index_num_vars],
                    'p': p[index_num_vars],
                    'n': num_vars,
                    'm/n': m_n[index_num_clauses]
                }
                results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
                
                with open(results_txt_file, 'a') as file_append:
                    file_append.write(f'{config}, {algorithm} Success: 0.0%, Total Flips: 0, Time: 0.00 seconds\n')
                print(f'{config}, {algorithm} Success: 0.0%, Total Flips: 0')
                continue
            
            iteration_start_time = time.time()

            # Generate a list of random seeds
            s = random.sample(range(1001), 100)
            walksat_success_rate = 0
            total_flips = 0
            
            # Test each seed for the given SAT solver configurations
            for seed in s:
                walksat_solver = WalkSAT(num_vars, num_clauses, k, seed, Q[index_num_vars], c[index_num_vars])
                success, tries, flips = walksat_solver.solve(max_flips[index_num_vars], max_tries, p[index_num_vars])
                if success:
                    walksat_success_rate += 1
                total_flips += flips * tries

            # Store the success rates
            success_rate = (walksat_success_rate / len(s)) * 100
            iteration_end_time = time.time()
            time_elapsed = iteration_end_time - iteration_start_time
            
            new_row = {
                'Configurations': config,
                'WalkSAT Success': success_rate,
                'Time (seconds)': time_elapsed,
                'Total Flips': total_flips,
                'c': c[index_num_vars],
                'Q': Q[index_num_vars],
                'p': p[index_num_vars],
                'n': num_vars,
                'm/n': m_n[index_num_clauses]
            }
            results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
            
            if success_rate == 0:
                consecutive_zero_success += 1
            else:
                consecutive_zero_success = 0
            
            with open(results_txt_file, 'a') as file_append:
                file_append.write(f'{config}, {algorithm} Success: {success_rate:.1f}%, Total Flips: {total_flips}, Time: {time_elapsed:.2f} seconds\n')
            print(f'{config}, {algorithm} Success: {success_rate:.1f}%, Total Flips: {total_flips}, Time: {time_elapsed:.2f} seconds')

            # Guardar resultados parciales en Excel después de cada configuración
            results_df.to_excel(results_excel_file, index=False)

    return results_df

# Configuración del experimento
experiment_number = "01"
experiment_name = f"WalkSAT_communities_mod{experiment_number}_c30_p05_tries3_flips10n"
print(experiment_name)
externo = False
excel = False

# Parámetros
n = [50, 100, 250, 500, 1000]
p = [0.5 for x in n]
c = [10 for x in n]
Q = [0.2 for x in n]

m_n = np.arange(2.5, 5.5, 0.1)
k = 3
algorithm = "WalkSAT"
max_tries = 3
max_flips_raw = 10
max_flips = [int(max_flips_raw*x) for x in n]

# Ejecutar el experimento
if not externo and not excel:
    results_df = run_experiment()
elif excel:
    results_df = pd.read_excel(f"results/00_Utilizadas/results_{experiment_name}.xlsx")

# Preparar datos para gráfico
if 'm/n' not in results_df.columns:
    # Si m/n no está en el DataFrame, calcularlo
    results_df['m/n'] = results_df['Configurations'].apply(lambda x: float(re.search(r'm/n=([\d.]+)', x).group(1)))

# Plotting
plt.figure(figsize=(10, 6))

# Agrupar por combinación única de parámetros (c, Q, p, n)
group_keys = results_df.groupby(['c', 'Q', 'p', 'n']).groups.keys()

for key in group_keys:
    mask = ((results_df['c'] == key[0]) & 
            (results_df['Q'] == key[1]) & 
            (results_df['p'] == key[2]) & 
            (results_df['n'] == key[3]))
    
    subset = results_df[mask]
    
    label = f"n={key[3]}"
    plt.scatter(subset['m/n'], subset['WalkSAT Success'], label=label)
    plt.plot(subset['m/n'], subset['WalkSAT Success'], linestyle='--')

plt.title(f"WalkSAT_communities_mod{experiment_number} - Clauses with one community")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances (%)")
plt.ylim(-5, 105)
plt.legend()

# Descomentar la siguiente línea para ajustar el espaciado de los subgráficos
# plt.tight_layout()
plt.savefig(f'results/results_{experiment_name}.png', bbox_inches='tight')
plt.show()