# -*- coding: utf-8 -*-
"""
Script principal mejorado para ejecutar experimentos
"""

from experiment_runner_parallel import run_experiment_parallel
import numpy as np
import multiprocessing
import os

MAX_WORKERS = max(1, multiprocessing.cpu_count() - 2)

def main():
    experiments = [
        # {
        #     "base_name": "WalkSAT_community_v00_flips&tries",
        #     "n": [50,100,250,500,1000],
        #     "p": [0.5],
        #     "c": [10],
        #     "Q": [0.8],
        #     "k": 3,
        #     "max_tries_values": [1,3,10],
        #     "max_flips_coef_values": [1,10,20],  # Usar coeficientes
        #     "max_flips_values": None,  # No usar valores fijos
        #     "m_n_ratios": np.arange(2.5, 5.5, 0.1),
        #     "num_seeds": 100,
        #     "algorithm_type": "WalkSAT_community" # GSAT, WalkSAT_community, WalkSAT_random
        # },
        # {
        #     "base_name": "WalkSAT_community_v02_prueba",
        #     "n": [1000],
        #     "p": [0.5],
        #     "c": [20],
        #     "Q": [0.8],
        #     "k": 3,
        #     "max_tries_values": [3],
        #     "max_flips_coef_values": [10],  # Usar coeficientes
        #     "max_flips_values": None,  # No usar valores fijos
        #     "m_n_ratios": np.arange(2.5, 4.5, 0.1),
        #     "num_seeds": 100,
        #     "algorithm_type": "WalkSAT_community" # GSAT, WalkSAT_community, WalkSAT_random
        # }
        {
            "base_name": "WalkSAT_community_vXX",
            "n": [500],
            "p": [0.5],
            "c": [20],
            "Q": [0.8],
            "k": 3,
            "max_tries_values": [3],
            "max_flips_coef_values": [10],  # Usar coeficientes
            "max_flips_values": None,  # No usar valores fijos
            "m_n_ratios": np.arange(2.5, 5.5, 0.1),
            "num_seeds": 100,
            "algorithm_type": "WalkSAT_community" # GSAT, WalkSAT_community, WalkSAT_random
        }
    ]

    for exp_config in experiments:
        experiment_name = exp_config["base_name"]
        
        print(f"\n{'='*60}")
        print(f"Configurando experimento: {experiment_name}")
        print(f"Cores disponibles: {multiprocessing.cpu_count()}")
        print(f"Workers utilizados: {MAX_WORKERS}")
        print(f"{'='*60}")
        
        # Verificar si el experimento ya está completo
        results_txt = f'results/results_{experiment_name}.txt'
        if os.path.exists(results_txt):
            print("\nAnalizando resultados previos...")
        
         # Asegurarse de que 'c' y 'Q' estén definidos para el algoritmo con Q y c
        c_values = exp_config.get("c", [None])
        Q_values = exp_config.get("Q", [None])

        # Ejecutar el experimento (con verificación interna)
        results = run_experiment_parallel(
            experiment_name=experiment_name,
            n_values=exp_config["n"],
            p_values=exp_config["p"] if exp_config["algorithm_type"] != "GSAT" else None,
            c_values=c_values if exp_config["algorithm_type"] == "WalkSAT_community" else None,
            Q_values=Q_values if exp_config["algorithm_type"] == "WalkSAT_community" else None,
            k=exp_config["k"],
            max_tries_values=exp_config["max_tries_values"],
            max_flips_values=exp_config.get("max_flips_values"),  # Usar get() por si no está definido
            max_flips_coef_values=exp_config.get("max_flips_coef_values"),  # Usar get() por si no está definido
            m_n_ratios=exp_config["m_n_ratios"],
            num_seeds=exp_config["num_seeds"],
            algorithm_type=exp_config["algorithm_type"]
        )

        # # Generar gráficos de rendimiento
        # generate_plots(
        #     experiment_name=experiment_name,
        #     results_df=results,
        #     plot_file=f'plots/performance_{experiment_name}.png',
        #     fixed_params={'Max Tries': 3, 'Q': 0.2, 'c': 10},  # Parámetros fijos para el gráfico
        #     flips_coef=10
        # )
        
        # print(f"\nEstado final del experimento '{experiment_name}':")
        # print(f"- Resultados: results/results_{experiment_name}.{{txt,xlsx}}")
        # print(f"- Gráfico: plots/performance_{experiment_name}.png")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()