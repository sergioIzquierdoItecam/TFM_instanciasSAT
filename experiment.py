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
    for num_vars in n:
        # Calculate the number of clauses based on num_vars and a base ratio array m
        m = (base_m * num_vars).astype(int)
        
        # Open a file to write experiment outputs for GSAT results
        with open(f'results/results_{algorithm}_{current_datetime}.txt', 'w') as file:
            for num_clauses in m:
                config = f'n={num_vars}, m={num_clauses}'
                results['Configurations'].append(config)
                iteration_start_time = time.time()

                # Generate a list of random seeds
                s = random.sample(range(1001), 100)
                gsat_success_rate = walksat_success_rate = 0
                
                # Test each seed for the given SAT solver configurations
                for seed in s:
                    if algorithm in ["both", "GSAT"]:
                        gsat_solver = GSAT(num_vars, num_clauses, k, seed)
                        if gsat_solver.solve(max_flips, max_tries)[0]:
                            gsat_success_rate += 1

                    if algorithm in ["both", "WalkSAT"]:
                        walksat_solver = WalkSAT(num_vars, num_clauses, k, seed)
                        if walksat_solver.solve(max_flips, max_tries, p)[0]:
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
                file.write(f'{config}, GSAT Success: {gsat_success_rate}%, WalkSAT Success: {walksat_success_rate}%, Time: {iteration_end_time - iteration_start_time:.2f} seconds\n')
                print(f'{config}, GSAT Success: {gsat_success_rate}%, WalkSAT Success: {walksat_success_rate}%, Time: {iteration_end_time - iteration_start_time:.2f} seconds')
    
    # Save the results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(f"results/results_{algorithm}_{current_datetime}.xlsx", index=False)

    return df

# Experiment configuration
n = [1000]  # Number of variables
base_m = np.array([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 5])  # Ratios of clauses to variables
k = 3  # Number of literals per clause
p = 0.5  # Probability parameter for WalkSAT
algorithm = "WalkSAT"  # Algorithm to use: "GSAT", "WalkSAT", or "both"
max_tries = 50
max_flips = 100

# Run the experiment
results_df = run_experiment(n, base_m, k, algorithm, p, max_tries, max_flips)

# Add m/n ratio for plotting results
results_df['m/n'] = base_m.tolist()*len(n)

# Plotting the results
plt.figure(figsize=(10, 6))
for i in range(len(n)):
    plt.scatter(results_df['m/n'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                results_df['GSAT Success'].iloc[len(base_m)*i:len(base_m)*(i+1)],
                label=f'n={n[i]} - GSAT',
                marker='o')
    
# Set the title and labels for the plot
plt.title("GSAT and WalkSAT Success Rates")
plt.xlabel("Ratio of Clauses to Variables (m/n)")
plt.ylabel("Percentage of Solved Instances")

# Add a legend to the plot
plt.legend()

# Save the plot to a file
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get the current date and time for file naming
plt.savefig(f'results/results_{algorithm}_{current_datetime}.png')

# Display the plot
plt.show()