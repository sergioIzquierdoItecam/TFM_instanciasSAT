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

# Function to run an experiment based on parameters
def run_experiment(n, m, k, algorithm="both", p=0.5, max_tries=50, max_flips=100):
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
                s = random.sample(range(1001), 100)
                gsat_success_rate = walksat_success_rate = 0
                
                # Test each seed for the given SAT solver configurations
                for seed in s:
                    # seed = 0
                    if algorithm in ["both", "GSAT"]:
                        gsat_solver = GSAT(num_vars, num_clauses, k, seed)
                        if gsat_solver.solve(max_flips[index_num_vars], max_tries)[0]:
                            gsat_success_rate += 1

                    if algorithm in ["both", "WalkSAT"]:
                        walksat_solver = WalkSAT(num_vars, num_clauses, k, seed)
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
# n = [50, 100, 250, 500, 1000]  # Number of variables
n = [1500, 2000, 2500, 5000, 10000]  # Number of variables
# n = [12, 20, 24, 40, 50, 100]  # Number of variables
# base_m = np.array([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])  # Ratios of clauses to variables
base_m = np.arange(3.5, 4.5, 0.1)  # Ratios of clauses to variables

# base_m = np.array([1, 1.5, 2, 2.5, 3, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 5])  # Ratios of clauses to variables
# base_m = np.arange(3,7,0.2)  # Ratios of clauses to variables
k = 3  # Number of literals per clause
p = 0.5  # Probability parameter for WalkSAT
algorithm = "WalkSAT"  # Algorithm to use: "GSAT", "WalkSAT", or "both"
# max_tries = 50
max_tries = 10
# max_flips = [50, 50, 50, 50, 50]
# max_flips = [int(x / 2) for x in n]
max_flips = 10*n
# GSAT - max_tries = 50, max_flips = 50

# Run the experiment
results_df = run_experiment(n, base_m, k, algorithm, p, max_tries, max_flips)

# Add m/n ratio for plotting results
results_df['m/n'] = base_m.tolist()*len(n)

# Plotting the results
plt.figure(figsize=(10, 6))
if algorithm in ["both", "GSAT"]:
    for i in range(len(n)):
        plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    label=f'n={n[i]} - GSAT',
                    marker='o')
if algorithm in ["both", "WalkSAT"]:
    for i in range(len(n)):
        plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['WalkSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    label=f'n={n[i]} - WalkSAT',
                    marker='o',
                    s=20)
        plt.plot(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    results_df['WalkSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                    linestyle='--')
        
# Set the title and labels for the plot
plt.title(f"WalkSAT and GSAT random - max tries={max_tries}, max flips=10n")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances")

# Add a legend to the plot
plt.legend()

# Save the plot to a file
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get the current date and time for file naming
plt.savefig(f'results/results_{algorithm}_{current_datetime}.png')

# Display the plot
plt.show()