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
from WalkSAT import WalkSAT
from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to run an experiment based on parameters
def run_experiment():
    # Dictionary to collect experiment results
    results = {'Configurations': [], 'WalkSAT Success': [], 'Time (seconds)': [], 'Total Flips': []}
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Loop over each variable count in n
    for index_num_vars,num_vars in enumerate(n):
        # Calculate the number of clauses based on num_vars and a base ratio array m
        m = (m_n * num_vars).astype(int)
        
        # Open a file to write experiment outputs for GSAT results
        for index_num_clauses, num_clauses in enumerate(m):
            config = f'p={p[index_num_vars]}, n={num_vars}, m/n={m_n[index_num_clauses]:.1f}'
            results['Configurations'].append(config)
            iteration_start_time = time.time()

            # Generate a list of random seeds
            s = random.sample(range(1001), 100)
            walksat_success_rate = 0
            total_flips = 0
            
            # Test each seed for the given SAT solver configurations
            for seed in s:
                walksat_solver = WalkSAT(num_vars, num_clauses, k, seed)
                success, tries, flips = walksat_solver.solve(max_flips[index_num_vars], max_tries, p[index_num_vars])
                if success:
                    walksat_success_rate += 1
                total_flips += flips * tries

        
            # Store the success rates in the results dictionary
            results['WalkSAT Success'].append((walksat_success_rate / len(s)) * 100)
            iteration_end_time = time.time()
            results['Time (seconds)'].append(iteration_end_time - iteration_start_time)
            results['Total Flips'].append(total_flips)
            success_rate = (walksat_success_rate) / len(s) * 100
            with open(f'results/results_{experiment_name}.txt', 'a') as file_append:
                file_append.write(f'{config}, {algorithm} Success: {success_rate:.1f}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
            print(f'{config}, {algorithm} Success: {success_rate:.1f}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds')
            # file.write(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
            # print(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')

    # Save the results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(f"results/results_{experiment_name}.xlsx", index=False)

    return df

# Nombre del experimento
experiment_name = "WalkSAT_random_ex01_flips10000n_prueba"
print(experiment_name)
externo = False
excel = False

n = [50]  # Número de variables
# Lista de probabilidades para WalkSAT
p = [0.5 for x in n]

# Configuración del experimento
# n = [50 for x in p]  # Número de variables
Q = [0.8 for x in p]
# 
m_n = np.arange(2.1, 5.5, 0.1)  # Ratios de cláusulas a variables
k = 3  # Número de literales por cláusula
algorithm = "WalkSAT"  # Algoritmo a usar: "GSAT", "WalkSAT", o "both"
max_tries = 1
max_flips = [int(10000*x) for x in n]

if externo:
    file_path = 'resultados.txt'  # Reemplaza con la ruta a tu archivo .txt
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                # Dividir y extraer los datos de cada línea
                parts = line.split(', ')
                p = float(parts[0].split('=')[1])
                n = int(parts[1].split('=')[1])
                m_n = float(parts[2].split('=')[1])
                walksat_success = float(parts[3].split(': ')[1].strip('%'))
                total_flips = int(parts[4].split(': ')[1])
                time_seconds = float(parts[5].split(': ')[1].strip(' seconds')) if len(parts)>5 else None
                data.append({'p': p, 'n': n, 'm/n': m_n, 'WalkSAT Success': walksat_success})
    results_df = pd.DataFrame(data)
    # Obtener valores únicos de n y filtrar datos
    p = results_df['p'].unique()
    n = results_df['n'].unique()
    m_n = results_df['m/n'].unique()
    results_df.to_excel(f"results/results_{experiment_name}.xlsx", index=False)
elif not(excel):
    # Run the experiment
    results_df = run_experiment()

    # Add m/n ratio for plotting results
    results_df['m/n'] = m_n.tolist()*len(n)
else:
    results_df = pd.read_excel(f"results/00_Utilizadas/results_{experiment_name}.xlsx")
    with open(f'results/results_{experiment_name}.txt', 'a') as file_append:
        for i in range(len(n)):
            for j in range(len(m_n)):
                config = f'p={p[i]}, n={n[i]}, m/n={m_n[j]:.1f}'
                success_rate = results_df['WalkSAT Success'].iloc[len(m_n) * i + j]
                total_flips = results_df['Total Flips'].iloc[len(m_n) * i + j]
                time_seconds = results_df['Time (seconds)'].iloc[len(m_n) * i + j]
                file_append.write(f'{config}, {algorithm} Success: {success_rate:.1f}%, Total Flips: {total_flips}, Time: {time_seconds:.2f} seconds\n')
    
    results_df['m/n'] = m_n.tolist()*len(n)



# Plotting the results
plt.figure(figsize=(10, 6))
for i in range(len(n)):
    plt.scatter(results_df['m/n'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                    results_df['WalkSAT Success'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                    label=f'n={n[i]}',
                    marker='o')
    plt.plot(results_df['m/n'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                results_df['WalkSAT Success'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                linestyle='--')
        
# Establecer el título y las etiquetas del gráfico
plt.title(f"{experiment_name} - p=0.5, max_tries={max_tries}, max_flips=100n")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances (%)")
plt.ylim(-5, 105)  # Establecer el rango del eje y

# Añadir una leyenda al gráfico
plt.legend()

# Guardar el gráfico en un archivo
plt.savefig(f'results/00_Utilizadas/results_{experiment_name}.png')

# Mostrar el gráfico
plt.show()