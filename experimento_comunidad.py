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
from WalkSAT_C00 import WalkSAT
# from WalkSAT_communities_modified import WalkSAT
from datetime import datetime

def leer_datos_archivo(nombre_archivo):
    datos= {'n':[], 'm/n': [], 'WalkSAT Success': [], 'time':[]}
    with open(nombre_archivo, 'r') as file:
        for line in file:
            partes = line.strip().split(', ')
            n_valor = int(partes[0].split('=')[1])
            m_n_ratio = float(partes[1].split('=')[1])
            walksat_success = float(partes[3].split(': ')[1].strip('%'))
            time = float(partes[4].split(' ')[1])
            # if n_valor not in datos:
            #     datos= {'m/n': [], 'WalkSAT Success': []}
            datos['n'].append(n_valor)
            datos['m/n'].append(m_n_ratio)
            datos['WalkSAT Success'].append(walksat_success)
            datos['time'].append(time)
    return pd.DataFrame(datos)


# Function to run an experiment based on parameters
def run_experiment(n, m, k, Q, c, algorithm="both", p=0.5, max_tries=50, max_flips=100):
    # Dictionary to collect experiment results
    results = {'Configurations': [], 'GSAT Success': [], 'WalkSAT Success': [], 'Time (seconds)': []}
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
                s = random.sample(range(1001), 200)
                gsat_success_rate = walksat_success_rate = 0
                
                # Test each seed for the given SAT solver configurations
                for seed in s:
                    seed = 0
                    if algorithm in ["both", "GSAT"]:
                        gsat_solver = GSAT(num_vars, num_clauses, k, seed)
                        if gsat_solver.solve(max_flips[index_num_vars], max_tries)[0]:
                            gsat_success_rate += 1

                    if algorithm in ["both", "WalkSAT"]:
                        walksat_solver = WalkSAT(num_vars, num_clauses, k, seed, Q[index_num_vars], c[index_num_vars])
                        # success, tries, flips = walksat_solver.solve(max_flips[index_num_vars], max_tries, p)
                        # n_clauses_max += n_clauses
                        if walksat_solver.solve(max_flips[index_num_vars], max_tries, p)[0]:
                        # if walksat_solver.solve(max_flips, max_tries, p)[0]:
                            walksat_success_rate += 1

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
                file.write(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
                print(f'{config}, GSAT Success: {gsat_success_rate / len(s)* 100}%, WalkSAT Success: {walksat_success_rate / len(s)* 100}%, Time: {iteration_end_time - iteration_start_time:.2f} seconds')#  Clauses: {n_clauses_max}')
    
    # Save the results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(f"results/results_{algorithm}_{current_datetime}.xlsx", index=False)

    return df


# Experiment configuration
n = [100,250,500,1000]  # Number of 
# n = [50,100,250,500,1000]  # Number of variables
# n = [1500, 2000, 5000, 10000]  # Number of variables
# n = [100,200,500]  # Number of variables
base_m = np.arange(1.5,3.5,0.1)  # Ratios of clauses to variables
# base_m = np.array([1, 1.5, 2, 2.5, 3, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 5])  # Ratios of clauses to variables
k = 3  # Number of literals per clause
Q = [0.8,0.8,0.8,0.8]
c = [30,30,30,30]
p = 0.5 # Probability parameter for WalkSAT
algorithm = "WalkSAT"  # Algorithm to use: "GSAT", "WalkSAT", or "both"
# max_tries = 50
max_tries = 10
max_flips = [int(x / 5) for x in n]
# max_flips = 10*n
# max_flips = [50]
# GSAT - max_tries = 50, max_flips = 50
print(f'Max tries: {max_tries}, Max flips: {max_flips}')

# Run the experiment
results_df = run_experiment(n, base_m, k, Q, c, algorithm, p, max_tries, max_flips)
# results_df = pd.read_excel('2.xlsx')

# current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get the current date and time for file naming
# results_df = leer_datos_archivo('results_WalkSAT.txt')
# results_df.to_excel(f"results/results_{algorithm}_{current_datetime}.xlsx", index=False)


# Add m/n ratio for plotting results
# results_df['m/n'] = base_m.tolist()*len(n)

# Plotting the results
plt.figure(figsize=(10, 6))
if algorithm in ["both", "GSAT"]:
    for i in range(len(n)):
        plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    label=f'n={n[i]} - GSAT',
                    marker='o',
                    s=20)
        plt.plot(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    linestyle='--')
if algorithm in ["both", "WalkSAT"]:
    for i in range(len(n)):
        plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['WalkSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    label=f'n={n[i]}, Q={Q[i]}, c={c[i]}',
                    marker='o',
                    s=20)
        plt.plot(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['WalkSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    linestyle='--')
    
# Set the title and labels for the plot
plt.title(f"WalkSAT community - max tries={max_tries}, max flips=n/5")
# plt.title(f"GSAT random - max tries=50, max flips=50")

plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances")

# Add a legend to the plot
plt.legend()

# Save the plot to a file
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get the current date and time for file naming
plt.savefig(f'results/results_{algorithm}_{current_datetime}.png')

# Display the plot
plt.show()