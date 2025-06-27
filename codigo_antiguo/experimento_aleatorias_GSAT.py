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
from GSAT import GSAT
from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to run an experiment based on parameters
def run_experiment():
    # Dictionary to collect experiment results
    results = {'Configurations': [], 'GSAT Success': [], 'Time (seconds)': [], 'Total Flips': []}
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Loop over each variable count in n
    for index_num_vars,num_vars in enumerate(n):
        # Calculate the number of clauses based on num_vars and a base ratio array m
        m = (m_n * num_vars).astype(int)
        
        # Open a file to write experiment outputs for GSAT results
        for index_num_clauses, num_clauses in enumerate(m):
            config = f'n={num_vars}, m/n={m_n[index_num_clauses]:.1f}'
            results['Configurations'].append(config)
            iteration_start_time = time.time()

            # Generate a list of random seeds
            s = random.sample(range(1001), 100)
            walksat_success_rate = 0
            total_flips = 0
            
            # Test each seed for the given SAT solver configurations
            for seed in s:
                walksat_solver = GSAT(num_vars, int(num_clauses), k, seed)
                success, tries, flips = walksat_solver.solve(max_flips[index_num_vars], max_tries)
                if success:
                    walksat_success_rate += 1
                total_flips += flips * tries

        
            # Store the success rates in the results dictionary
            results['GSAT Success'].append((walksat_success_rate / len(s)) * 100)
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
experiment_name = "GSAT_random_ex01_flips250"
print(experiment_name)
externo = True

# Configuración del experimento
n = [250]  # Número de variables
m_n = np.arange(2.7, 3, 0.1)  # Ratios de cláusulas a variables
k = 3  # Número de literales por cláusula
algorithm = "GSAT"  # Algoritmo a usar: "GSAT", "WalkSAT", o "both"
# max_tries = 50
# max_flips = [100 for x in n]
max_tries = 50
max_flips = [250 for x in n]

if externo:
    file_path = 'resultados.txt'  # Reemplaza con la ruta a tu archivo .txt
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                # Dividir y extraer los datos de cada línea
                parts = line.split(', ')
                n = int(parts[0].split('=')[1])
                m_n = float(parts[1].split('=')[1])
                gsat_success = float(parts[2].split(': ')[1].strip('%'))
                total_flips = int(parts[3].split(': ')[1])
                time_seconds = float(parts[4].split(': ')[1].strip(' seconds')) if len(parts)>4 else None
                data.append({'n': n, 'm/n': m_n, 'GSAT Success': gsat_success, 'Total Flips': total_flips, 'Time (seconds)': time_seconds})
    results_df = pd.DataFrame(data)
    # Obtener valores únicos de n y filtrar datos
    m_n = results_df['m/n'].unique()
    n = results_df['n'].unique()
    results_df.to_excel(f"results/results_{experiment_name}.xlsx", index=False)
else:
    # Run the experiment
    results_df = run_experiment()

    # Add m/n ratio for plotting results
    results_df['m/n'] = m_n.tolist()*len(n)

# Plotting the results
plt.figure(figsize=(10, 6))
for i in range(len(n)):
    plt.scatter(results_df['m/n'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                    results_df['GSAT Success'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                    label=f'n={n[i]}',
                    marker='o')
    plt.plot(results_df['m/n'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                results_df['GSAT Success'].iloc[len(m_n) * i:len(m_n) * (i + 1)],
                linestyle='--')
        
# Establecer el título y las etiquetas del gráfico
plt.title(f"{experiment_name}, max_tries={max_tries}, max_flips={max_flips[0]}")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances (%)")
plt.ylim(-5, 105)  # Establecer el rango del eje y

# Añadir una leyenda al gráfico
plt.legend()

# Guardar el gráfico en un archivo
plt.savefig(f'results/00_Utilizadas/results_{experiment_name}.png')

# Mostrar el gráfico
plt.show()