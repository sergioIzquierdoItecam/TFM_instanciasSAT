# -*- coding: utf-8 -*-
"""
Main script para ejecutar experimentos con WalkSAT
"""

import os
import datetime
from experiment_runner import run_experiment

def generate_experiment_name(base_name, params):
    """Genera un nombre único para el experimento basado en parámetros"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    param_str = "_".join(f"{k}{v}" for k,v in params.items() if k != 'base_name')
    return f"{base_name}_{param_str}"

def main():
    # Configuración base de experimentos
    experiments = [
        {
            "base_name": "WalkSAT_communities",
            "n": [50, 100, 250, 500, 1000],  # Diferentes tamaños de problemas
            "p": [0.5],                       # Probabilidad de noise walk
            "c": [10],                        # Número de comunidades
            "Q": [0.2],                       # Probabilidad de cláusula intra-comunidad
            "k": 3,                           # Tamaño de cláusulas
            "max_tries": 3,                   # Número máximo de intentos
            "max_flips_coef": 10,             # Coeficiente para flips máximos (max_flips = coef * n)
            "m_n_ratios": np.arange(2.5, 5.5, 0.1)  # Ratios m/n a probar
        },
        # Puedes añadir más configuraciones de experimentos aquí
        # {
        #     "base_name": "WalkSAT_variable_Q",
        #     "n": [500],
        #     "p": [0.3, 0.5, 0.7],
        #     "c": [10],
        #     "Q": [0.1, 0.3, 0.5, 0.7, 0.9],
        #     ...
        # }
    ]

    for exp_config in experiments:
        # Generar nombre del experimento
        experiment_name = generate_experiment_name(
            exp_config["base_name"],
            {k: v[0] if isinstance(v, list) and len(v) == 1 else "var" 
             for k, v in exp_config.items() if k != "base_name"}
        )

        print(f"\n{'='*50}")
        print(f"Iniciando experimento: {experiment_name}")
        print(f"Configuración: {exp_config}")
        print(f"{'='*50}\n")

        # Ejecutar el experimento para cada combinación de parámetros
        # (Aquí simplificamos ejecutando todas las combinaciones, podrías añadir más lógica)
        run_experiment(
            experiment_name=experiment_name,
            n_values=exp_config["n"],
            p_values=exp_config["p"],
            c_values=exp_config["c"],
            Q_values=exp_config["Q"],
            k=exp_config["k"],
            max_tries=exp_config["max_tries"],
            max_flips_coef=exp_config["max_flips_coef"],
            m_n_ratios=exp_config["m_n_ratios"]
        )

if __name__ == "__main__":
    import numpy as np
    main()