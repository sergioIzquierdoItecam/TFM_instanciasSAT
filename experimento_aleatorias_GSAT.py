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
from WalkSAT import WalkSAT
from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to run an experiment based on parameters
def run_experiment(n, m, k, algorithm="both", max_tries=50, max_flips=100):
    # Dictionary to collect experiment results
    results = {'Configurations': [], 'GSAT Success': [], 'WalkSAT Success': [], 'Time (seconds)': [], 'Total Flips': []}
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Loop over each variable count in n
    for index_num_vars,num_vars in enumerate(n):
        # Calculate the number of clauses based on num_vars and a base ratio array m
        m = (base_m * num_vars).astype(int)
        n_clauses_max = 0
        
        # Open a file to write experiment outputs for GSAT results
        with open(f'results/results_{algorithm}_{current_datetime}.txt', 'w') as file:
            for num_clauses in m:
                config = f'n={num_vars}, m/n={num_clauses/num_vars}'
                results['Configurations'].append(config)
                iteration_start_time = time.time()

                # Generate a list of random seeds
                s = random.sample(range(1001), 100)
                gsat_success_rate = walksat_success_rate = 0
                gsat_total_flips = gsat_total_tries = 0
                walksat_total_flips = walksat_total_tries = 0
                total_flips = total_tries = 0
                
                # Test each seed for the given SAT solver configurations
                tasks = []
                # with ThreadPoolExecutor() as executor:
                for seed in s:
                    if algorithm in ["both", "GSAT"]:
                        gsat_solver = GSAT(num_vars, num_clauses, k, seed)
                        success, tries, flips = gsat_solver.solve(max_flips[index_num_vars], max_tries)
                        if success:
                            gsat_success_rate += 1
                        total_flips += flips * tries
                        # total_tries += tries

                # Store the success rates in the results dictionary
                if algorithm in ["both", "GSAT"]:
                    results['GSAT Success'].append((gsat_success_rate / len(s)) * 100)
                else:
                    results['GSAT Success'].append(np.nan)
                if algorithm in ["both", "WalkSAT"]:
                    results['WalkSAT Success'].append((walksat_success_rate / len(s)) * 100)
                else:
                    results['WalkSAT Success'].append(np.nan)

                iteration_end_time = time.time()
                results['Time (seconds)'].append(iteration_end_time - iteration_start_time)
                results['Total Flips'].append(total_flips)
                success_rate = (gsat_success_rate + walksat_success_rate) / len(s) * 100
                file.write(f'{config}, {algorithm} Success: {success_rate}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
                print(f'{config}, {algorithm} Success: {success_rate}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds')
                # file.write(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
                # print(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Total Flips: {total_flips}, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
    
    # Save the results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(f"results/results_{algorithm}_{current_datetime}.xlsx", index=False)

    return df

# Configuración del experimento
n = [50,100,250,500,1000]  # Número de variables
base_m = np.arange(3.5, 5.5, 0.1)  # Ratios de cláusulas a variables
k = 3  # Número de literales por cláusula
algorithm = "GSAT"  # Algoritmo a usar: "GSAT", "WalkSAT", o "both"
max_tries = 50
max_flips = [int(50) for x in n]

externo = True

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
                gsat_success = float(parts[2].split(': ')[1].strip('%')) if 'GSAT Success' in parts[2] else None
                data.append({'n': n, 'm/n': m_n, 'GSAT Success': gsat_success})
    results_df = pd.DataFrame(data)
    # Obtener valores únicos de n y filtrar datos
    n = results_df['n'].unique()
    base_m = results_df['m/n'].unique()
else:
    # Run the experiment
    results_df = run_experiment(n, base_m, k, algorithm, max_tries, max_flips)

    # Add m/n ratio for plotting results
    results_df['m/n'] = base_m.tolist()*len(n)



# Plotting the results
plt.figure(figsize=(10, 6))
for i in range(len(n)):
    plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                label=f'n={n[i]}',
                marker='o')
    plt.plot(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
        results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
        linestyle='--')

# Establecer el título y las etiquetas del gráfico
plt.title(f"GSAT random - max_tries={max_tries}, max_flips={max_flips[0]}")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances (%)")

# Añadir una leyenda al gráfico
plt.legend(loc='upper right')

# Guardar el gráfico en un archivo
plt.savefig(f'results/results_WalkSAT_max_tries={max_tries}_max_flips={max_flips[0]}.png')

# Mostrar el gráfico
plt.show()
