# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 20:22:24 2024

@author: Sergio
"""

import subprocess
import random

class GSAT:
    # Initialization method with parameters to define the SAT problem
    def __init__(self, variables, clauses, clauseLength, seed):
        self.variables = variables  # Number of variables in the formula
        self.clauses = clauses       # Number of clauses in the formula
        self.clauseLength = clauseLength  # Number of literals per clause
        self.seed = seed            # Seed for randomness
        self.formula = self.generate_random_model()  # Generate the initial random SAT formula

    # Method to generate a random model using external program
    def generate_random_model(self):
        # Path to the random model generator executable
        path_generator_model = "./communityAttachment/commAttach"
        # Arguments for the random model generator
        arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                      '-k', str(self.clauseLength), '-c', str(self.communities),
                      '-Q', str(self.modularity), '-s', str(self.seed)]
        process = subprocess.Popen([path_generator_model] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        decoded_output = output.decode("utf-8")
        file_formula = "community_formula.txt"
        with open(file_formula, "w") as file:
            file.write(decoded_output)
            
        path_features_s = "./graph_features_sat_v_2_2/features_s"
        file_communities = "communities.txt"
        arguments = ["-5", "-q", file_communities, file_formula]
        process = subprocess.Popen([path_features_s] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        # decoded_output = output.decode("utf-8")
        with open(file_communities, "r") as file:
            lines = file.readlines()
        communities_variables = []
        for index, line in enumerate(lines, start=1):
            # Elimina cualquier espacio en blanco al principio o final de la línea
            value = line.strip()
            # Almacena en el diccionario la fila (indice) como clave y el valor convertido a entero como valor
            communities_variables.append(int(value))
        
        contador = Counter(communities_variables)
        limite = 1
        cantidad_mayor_que_limite = sum(1 for count in contador.values() if count > limite)
        
        # Parse the output to form the SAT formula as a list of lists
        formula = [[int(value) for value in line.split()[:-1]] for line in decoded_output.splitlines()[8:]]
        return formula, communities_variables

    # Evaluate a given variable assignment against the formula
    def evaluate_formula(self, assignment):
        # Dictionary to keep track of which clauses are satisfied
        satisfied = {clause+1: False for clause in range(self.clauses)}
        # Check each clause to see if it is satisfied by the current assignment
        for clause in range(1, self.clauses + 1):
            satisfied[clause] = False
            for literal in self.formula[clause-1]:
                if (literal > 0 and assignment[abs(literal)]) or (literal < 0 and not assignment[abs(literal)]):
                    satisfied[clause] = True
                    break
        return satisfied

    # Get a dictionary linking variables to the clauses they appear in
    def get_variable_clauses(self, assignment):
        variable_clauses = {}
        score_clauses = {}
        for clause_index, clause in enumerate(self.formula, start=1):
            for literal in clause:
                if assignment[abs(literal)]:
                    variable = literal
                else:
                    variable = -literal
                if variable not in variable_clauses:
                    variable_clauses[variable] = []
                variable_clauses[variable].append(clause_index)
                if clause_index not in score_clauses:
                    score_clauses[clause_index] = 0
                if variable > 0:
                    score_clauses[clause_index] += 1
        return variable_clauses, score_clauses
    
    # def get_score_clauses(self, assignment):
    #     score_clauses = {}
    #     for clause_index, clause in enumerate(self.formula, start=1):
    #         for literal in clause:
    #             variable = literal
    #             if clause_index not in score_clauses:
    #                 score_clauses[clause_index] = 0
    #             if (variable > 0 and assignment[abs(variable)]) or (variable < 0 and not(assignment[abs(variable)])):
    #                 score_clauses[clause_index] += 1
    #     return score_clauses


    # Count how many clauses are satisfied in total
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to solve the SAT problem using a max flips and max tries approach
    def solve(self, max_flips, max_tries):
        # variable_clauses = self.get_variable_clauses()  # Mapping of variables to clauses
        # satisfied = {clause+1: False for clause in range(self.clauses)}  # Initial state of clause satisfaction
        
        for tries in range(max_tries):
            # Random initial assignment
            # random.seed(0)
            assignment = {variable+1: random.choice([True, False]) for variable in range(self.variables)}
            variable_clauses,score_clauses = self.get_variable_clauses(assignment) 
            # score_clauses = self.get_score_clauses(assignment)            
            for flips in range(max_flips):
                # score_clauses = self.get_score_clauses(assignment)  
                               

                satisfied_total = 0 
                for clauses in score_clauses:
                    if score_clauses[clauses] != 0:
                        satisfied_total += 1
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries, flips               
            
                
                break_count_min = self.clauses
                # variable_break_count_min = 0
                score_clauses_auxiliar = score_clauses.copy()
                
                for variable in range(1,self.variables+1):
                    satisfied_total_auxiliar = satisfied_total
                    if variable in variable_clauses: 
                        for clause in variable_clauses[variable]:
                            if score_clauses_auxiliar[clause] == 1:
                                satisfied_total_auxiliar -= 1
                            score_clauses_auxiliar[clause] -= 1 
                    if -variable in variable_clauses: 
                        for clause in variable_clauses[-variable]:
                            if score_clauses_auxiliar[clause] == 0:
                                satisfied_total_auxiliar += 1
                            score_clauses_auxiliar[clause] += 1
                                    
                # for variable in range(1,self.variables):
                    # score_clauses_auxiliar = score_clauses.copy()
                    # satisfied_total_auxiliar = satisfied_total
                    # for clause in variable_clauses[variable]:
                    #     if (variable > 0 and assignment[abs(variable)]) or (variable < 0 and not(assignment[abs(variable)])):
                            
                    # if (variable > 0 and assignment[abs(variable)]) or (variable < 0 and not(assignment[abs(variable)])):
                        
                    #     score_variable = -1
                    # else:
                    #     # clauses_satisfied 
                    #     score_variable = 1
                    # if variable in variable_clauses: 
                    #     for clause in variable_clauses[variable]:
                    #         # score_clauses_auxiliar[clause] += score_variable
                    #         if score_clauses[variable]
                    #         satisfied_total_auxiliar += score_variable                       
                    # if -variable in variable_clauses: 
                    #     for clause in variable_clauses[-variable]:
                    #         # score_clauses_auxiliar[clause] += score_variable
                    #         satisfied_total_auxiliar -= score_variable
                        

                    break_count = self.clauses - satisfied_total_auxiliar
                    if satisfied_total_auxiliar == self.clauses:
                        return True, tries, flips
                    elif break_count < break_count_min:
                        break_count_min = break_count
                        # variable_break_count_min = abs(variable)
                        score_clauses_min = score_clauses_auxiliar.copy()

                # assignment[variable_break_count_min] = not assignment[variable_break_count_min]
                score_clauses = score_clauses_min.copy()
        
        # Return the final result after all tries and flips
        return False, max_tries, max_flips
