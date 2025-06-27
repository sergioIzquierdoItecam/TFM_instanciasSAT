# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 20:34:02 2024

@author: Sergio
"""

# Modified 01 WalkSAT solver: clauses with one community 

import subprocess
import random
import comprueba_SAT
import tempfile
import shutil
import os

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
    
    # Generates a random SAT model using an external program
    def generate_random_model(self):
        # Crear directorio temporal único para este proceso
        temp_dir = tempfile.mkdtemp()
        file_formula = os.path.join(temp_dir, "community_formula.txt")
        file_communities = os.path.join(temp_dir, "communities.txt")
        
        try:
            path_generator_model = "./communityAttachment/commAttach"
            arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                        '-k', str(self.clauseLength), '-c', str(self.communities),
                        '-Q', str(self.modularity), '-s', str(self.seed)]
            
            process = subprocess.Popen(
                [path_generator_model] + arguments, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            decoded_output = output.decode("utf-8")
            
            with open(file_formula, "w") as file:
                file.write(decoded_output)
    
            path_features_s = "./graph_features_sat_v_2_2/features_s"
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
        
        finally:
            # Limpiar los archivos temporales
            shutil.rmtree(temp_dir)

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
        for clause_index in range(1,self.clauses + 1):
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

                if variable > 0:
                    score_clauses[clause_index] += 1
        return variable_clauses, score_clauses, clause_assignment

    # Calculates the total number of clauses that are satisfied
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to attempt solving the SAT problem, allowing flips and retries
    def solve(self, max_flips, max_tries, probability):
        for tries in range(max_tries):
            # Random initial assignment
            assignment = {variable + 1: random.choice([True, False]) for variable in range(self.variables)}
            variable_clauses, score_clauses, clause_assignment = self.get_variable_clauses(assignment)
            file_assignment = "random_assignment.txt"

            # Check if initial assignment is solution
            satisfied_total = sum(1 for clauses in score_clauses if score_clauses[clauses] != 0)
            if satisfied_total == self.clauses:
                with open(file_assignment, "w") as file:
                    file.write(str(assignment))
                return True, tries+1, 1

            for flips in range(max_flips):
                # Get unsatisfied clauses
                clauses_unsatisfied = [key for key, value in score_clauses.items() if value == 0]
                
                # Group unsatisfied clauses by community and count them
                community_unsatisfied = {}
                for clause in clauses_unsatisfied:
                    # Assuming clause_community_count is a list where index is clause-1
                    # and contains a dict of {community_id: count}
                    communities = self.clause_community_count[clause-1]
                    main_community = max(communities.items(), key=lambda x: x[1])[0]
                    community_unsatisfied[main_community] = community_unsatisfied.get(main_community, 0) + 1
                
                # Sort communities by number of unsatisfied clauses (descending)
                sorted_communities = sorted(community_unsatisfied.items(), 
                                        key=lambda x: x[1], reverse=True)
                
                # Try to find a clause from the most problematic communities first
                selected_clause = None
                for community, count in sorted_communities:
                    # Get clauses from this community that are unsatisfied
                    community_clauses = [
                        c for c in clauses_unsatisfied 
                        if max(self.clause_community_count[c-1].items(), key=lambda x: x[1])[0] == community
                    ]
                    if community_clauses:
                        selected_clause = random.choice(community_clauses)
                        break
                
                # If no community-based selection worked, fall back to random
                if selected_clause is None and clauses_unsatisfied:
                    selected_clause = random.choice(clauses_unsatisfied)
                elif not clauses_unsatisfied:
                    continue  # all clauses satisfied (shouldn't happen here)
                
                # Rest of your flipping logic remains the same
                freebie_move = False
                score_clauses_auxiliar = {}
                break_count = {}
                satisfied_total_auxiliar = {}
                clause_assignment_auxiliar = {}
                
                for variable in clause_assignment[selected_clause]:
                    break_count[variable] = 0
                    score_clauses_auxiliar[variable] = score_clauses.copy()
                    satisfied_total_auxiliar[variable] = satisfied_total
                    clause_assignment_auxiliar[variable] = clause_assignment.copy()
                    
                    for clause in variable_clauses[variable]:
                        if variable > 0:
                            if score_clauses_auxiliar[variable][clause] == 1:
                                break_count[variable] += 1
                                satisfied_total_auxiliar[variable] -= 1

                            if score_clauses_auxiliar[variable][clause] != 0:
                                score_clauses_auxiliar[variable][clause] -= 1
 
                        else:
                            if score_clauses_auxiliar[variable][clause] == 0:
                                satisfied_total_auxiliar[variable] += 1
                            if score_clauses_auxiliar[variable][clause] != 3:
                                score_clauses_auxiliar[variable][clause] += 1

                        for i in range(len(clause_assignment_auxiliar[variable][clause])):
                            if clause_assignment_auxiliar[variable][clause][i] == variable or clause_assignment_auxiliar[variable][clause][i] == -variable:
                                clause_assignment_auxiliar[variable][clause][i] = -clause_assignment_auxiliar[variable][clause][i]

                    # If exists -variable calculate its score clauses            
                    if -variable in variable_clauses:
                        for clause in variable_clauses[-variable]:
                            if variable>0:
                                if score_clauses_auxiliar[variable][clause] == 0:
                                    satisfied_total_auxiliar[variable] += 1
                                if score_clauses_auxiliar[variable][clause] != 3:
                                    score_clauses_auxiliar[variable][clause] += 1
                            else:
                                if score_clauses_auxiliar[variable][clause] == 1:
                                    break_count[variable] += 1
                                    satisfied_total_auxiliar[variable] -= 1
                                if score_clauses_auxiliar[variable][clause] != 0:
                                    score_clauses_auxiliar[variable][clause] -= 1 

                            for i in range(len(clause_assignment_auxiliar[variable][clause])):
                                if clause_assignment_auxiliar[variable][clause][i] == variable or clause_assignment_auxiliar[variable][clause][i] == -variable:
                                    clause_assignment_auxiliar[variable][clause][i] = -clause_assignment_auxiliar[variable][clause][i]
        
                
                    if break_count[variable] == 0:
                        variable_flip = variable
                        freebie_move = True
                        break

                if not freebie_move:
                    if random.random() <= probability:
                        variable_flip = random.choice(list(break_count.keys()))
                    else:
                        variable_flip = min(break_count, key=lambda k: break_count[k])  
                            
                score_clauses = score_clauses_auxiliar[variable_flip].copy()
                satisfied_total = satisfied_total_auxiliar[variable_flip]
                
                if variable_flip in variable_clauses and -variable_flip in variable_clauses:
                    variable_clauses_aux = variable_clauses[-variable_flip]
                    variable_clauses[-variable_flip] = variable_clauses[variable_flip]
                    variable_clauses[variable_flip] = variable_clauses_aux
                elif variable_flip in variable_clauses:
                    variable_clauses[-variable_flip] = variable_clauses[variable_flip]
                elif -variable_flip in variable_clauses:
                    variable_clauses[variable_flip] = variable_clauses[-variable_flip]
                    
                assignment[abs(variable_flip)] = not assignment[abs(variable_flip)] 
                clause_assignment = clause_assignment_auxiliar[variable_flip].copy()

                if satisfied_total == self.clauses:
                    with open(file_assignment, "w") as file:
                        file.write(str(assignment))
                    return True, tries+1, flips+1

        return False, max_tries, max_flips
