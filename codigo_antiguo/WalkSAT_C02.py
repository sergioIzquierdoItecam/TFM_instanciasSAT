# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 20:34:02 2024

@author: Sergio
"""

import subprocess
import random
from collections import Counter


class WalkSAT:
    # Initialize the WalkSAT solver with the given parameters
    def __init__(self, variables, clauses, clauseLength, seed, modularity, communities):
        self.variables = variables  # Number of variables in the formula
        self.clauses = clauses       # Number of clauses in the formula
        self.clauseLength = clauseLength  # Number of literals per clause
        self.seed = seed            # Seed for randomness
        self.modularity = modularity
        self.communities = communities
        # Generate the initial random SAT formula
        self.formula, self.communities_variables, self.variable_to_community, self.clause_community_count = self.generate_random_model()
    
    def generate_random_model(self):
        # Path to the random model generator executable
        path_generator_model = "./communityAttachment/commAttach"
        # Arguments for the random model generator
        arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                     '-k', str(self.clauseLength), '-c', str(self.communities),
                     '-Q', str(self.modularity), '-s', str(self.seed)]
        process = subprocess.Popen(
            [path_generator_model] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        decoded_output = output.decode("utf-8")
        file_formula = "community_formula.txt"
        with open(file_formula, "w") as file:
            file.write(decoded_output)
    
        path_features_s = "./graph_features_sat_v_2_2/features_s"
        file_communities = "communities.txt"
        arguments = ["-5", "-q", file_communities, file_formula]
        process = subprocess.Popen(
            [path_features_s] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        
        with open(file_communities, "r") as file:
            lines = file.readlines()
    
        # Crear un diccionario que mapea comunidades a listas de variables
        community_to_vars = {}
        for var, line in enumerate(lines, start=1):
            community = int(line.strip())
            if community not in community_to_vars:
                community_to_vars[community] = []
            community_to_vars[community].append(var)
    
        # Crear el diccionario final communities_variables
        communities_variables = {}
        for var_list in community_to_vars.values():
            if len(var_list) > 1:  # Solo considerar comunidades con más de una variable
                for var in var_list:
                    communities_variables[var] = [v for v in var_list if v != var]
        
        # Crear el diccionario variable_to_community solo con variables en comunidades con más de una variable
        variable_to_community = {var: community for community, vars_list in community_to_vars.items() if len(vars_list) > 1 for var in vars_list}
    
        # Parse the output to form the SAT formula as a list of lists
        formula = [[int(value) for value in line.split()[:-1]]
                   for line in decoded_output.splitlines()[8:]]
    
        # Crear el diccionario clause_community_count
        clause_community_count = []
        for clause in formula:
            community_count = {}
            for var in clause:
                var_abs = abs(var)
                if var_abs in variable_to_community:
                    community = variable_to_community[var_abs]
                    if community in community_count:
                        community_count[community] += 1
                    else:
                        community_count[community] = 1
            clause_community_count.append(community_count)
    
        return formula, communities_variables, variable_to_community, clause_community_count

    # Evaluates the given assignment to determine which clauses are satisfied
    def evaluate_formula(self, assignment, satisfied, clauses=None):
        if clauses is None:
            clauses = range(1, self.clauses + 1)
        for clause in clauses:
            satisfied[clause] = False
            for literal in self.formula[clause-1]:
                if (literal > 0 and assignment[abs(literal)]) or (literal < 0 and not assignment[abs(literal)]):
                    satisfied[clause] = True
                    break
        return satisfied

    # Builds a map of variables to the clauses they appear in
    def get_variable_clauses(self, assignment):
        variable_clauses = {}
        score_clauses = {}
        clause_assignment = {}
        for clause_index in range(1, self.clauses + 1):
            # for clause_index, clause in enumerate(self.formula, start=1):
            clause = self.formula[clause_index - 1]
            score_clauses[clause_index] = 0
            clause_assignment[clause_index] = []

            for literal in clause:
                if assignment[abs(literal)]:
                    variable = literal
                else:
                    variable = -literal
                clause_assignment[clause_index].append(variable)

                if variable not in variable_clauses:
                    variable_clauses[variable] = []
                variable_clauses[variable].append(clause_index)
                # if clause_index not in score_clauses:
                #     score_clauses[clause_index] = 0
                if variable > 0:
                    score_clauses[clause_index] += 1
        return variable_clauses, score_clauses, clause_assignment

    # Calculates the total number of clauses that are satisfied
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to attempt solving the SAT problem, allowing flips and retries
    def solve(self, max_flips, max_tries, probability):
        # Initialize all clauses as unsatisfied
        satisfied = {clause + 1: False for clause in range(self.clauses)}

        n_variable_clauses = 0

        for tries in range(max_tries):
            # Randomly assign True/False to each variable
            # random.seed(0)
            assignment = {
                variable + 1: random.choice([True, False]) for variable in range(self.variables)}
            variable_clauses, score_clauses, clause_assignment = self.get_variable_clauses(
                assignment)

            for flips in range(max_flips):

                satisfied_total = 0
                for clauses in score_clauses:
                    if score_clauses[clauses] != 0:
                        satisfied_total += 1
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries+1, flips+1
                

                clauses_unsatisfied = [
                    key for key, value in score_clauses.items() if value == 0 and max(self.clause_community_count[key-1].values()) == 3]
                
                if len(clauses_unsatisfied) == 0:
                    clauses_unsatisfied = [key for key, value in score_clauses.items() if value == 0]                 
                clause_unsatisfied = random.choice(clauses_unsatisfied)
                
                if flips == 0:
                    variables_flip_initial = []
                    for clause in clauses_unsatisfied:
                        variables_flip_initial.append(random.choice(self.formula[clause-1]))       
                    for variable in variables_flip_initial:
                        assignment[abs(variable)] = not(assignment[abs(variable)])
                    variable_clauses, score_clauses, clause_assignment = self.get_variable_clauses(
                        assignment)
                    satisfied_total = 0
                    for clauses in score_clauses:
                        if score_clauses[clauses] != 0:
                            satisfied_total += 1
                    if satisfied_total == self.clauses:  # If all clauses are satisfied
                        return True, tries, flips
                    

                freebie_move = False

                score_clauses_auxiliar = {}
                break_count = {}
                satisfied_total_auxiliar = {}

                for variable in clause_assignment[clause_unsatisfied]:
                    # for variable in self.formula[clause_unsatisfied - 1]:

                    break_count[variable] = 0
                    score_clauses_auxiliar[variable] = score_clauses.copy()
                    satisfied_total_auxiliar[variable] = satisfied_total

                    for clause in variable_clauses[variable]:
                        if variable > 0:
                            if score_clauses_auxiliar[variable][clause] == 1:
                                break_count[variable] += 1
                                satisfied_total_auxiliar[variable] -= 1
                            score_clauses_auxiliar[variable][clause] -= 1

                        else:
                            if score_clauses_auxiliar[variable][clause] == 0:
                                satisfied_total_auxiliar[variable] += 1
                            score_clauses_auxiliar[variable][clause] += 1
                                
                    if -variable in variable_clauses:
                        for clause in variable_clauses[-variable]:
                            if variable>0:
                                if score_clauses_auxiliar[variable][clause] == 0:
                                    satisfied_total_auxiliar[variable] += 1
                                score_clauses_auxiliar[variable][clause] += 1
                            else:
                                if score_clauses_auxiliar[variable][clause] == 1:
                                    break_count[variable] += 1
                                    satisfied_total_auxiliar[variable] -= 1
                                score_clauses_auxiliar[variable][clause] -= 1

                # for variable in clause_assignment[clause_unsatisfied]:
                    # If variable is in a community flip
                    # if break_count[variable] == 0 and abs(variable) in self.communities_variables:
                    if break_count[variable] == 0:
                        variable_flip = variable
                        freebie_move = True
                        break

                if not freebie_move:
                    # With a certain probability, choose a random flip or the best found flip
                    if random.random() <= probability:
                        variable_flip = random.choice(list(break_count.keys()))
                    else:
                        variable_flip = min(
                            break_count, key=lambda k: break_count[k])

                score_clauses = score_clauses_auxiliar[variable_flip].copy()
                satisfied_total = satisfied_total_auxiliar[variable_flip]

                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries+1, flips+1

        # After all the attempts, if a solution has not been found, return failure
        # satisfied_total = self.get_satisfied_total(satisfied)
        return False, max_tries, max_flips
