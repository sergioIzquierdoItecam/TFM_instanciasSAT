# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 20:34:02 2024

@author: Sergio
"""

import subprocess
import random

class WalkSAT:
    # Initialize the WalkSAT solver with the given parameters
    def __init__(self, variables, clauses, clauseLength, seed):
        self.variables = variables  # Total number of variables in the SAT formula
        self.clauses = clauses  # Total number of clauses in the SAT formula
        self.clauseLength = clauseLength  # Number of literals in each clause
        self.seed = seed  # Random seed for reproducibility
        self.formula = self.generate_random_model()  # Generate the formula randomly based on input parameters

    # Generates a random SAT model using an external program
    def generate_random_model(self):
        path_generator_model = "./communityAttachment/random"  # Path to the external model generator
        arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                     '-k', str(self.clauseLength), '-s', str(self.seed)]
        process = subprocess.Popen([path_generator_model] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        decoded_output = output.decode("utf-8")
        # Parse the output to form the SAT formula as a list of lists
        formula = [[int(value) for value in line.split()[:-1]] for line in decoded_output.splitlines()[6:]]
        return formula

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
        satisfied = {clause + 1: False for clause in range(self.clauses)}  # Initialize all clauses as unsatisfied
        
        n_variable_clauses = 0
        
        for tries in range(max_tries):
            # Randomly assign True/False to each variable
            # random.seed(0)
            assignment = {variable + 1: random.choice([True, False]) for variable in range(self.variables)}
            variable_clauses, score_clauses, clause_assignment = self.get_variable_clauses(assignment) 

            for flips in range(max_flips):
                
                satisfied_total = 0 
                for clauses in score_clauses:
                    if score_clauses[clauses] != 0:
                        satisfied_total += 1
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries, flips                
                
                clauses_unsatisfied = [key for key, value in score_clauses.items() if value==0]
                clause_unsatisfied = random.choice(clauses_unsatisfied)
                
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
                        if variable > 0 and score_clauses_auxiliar[variable][clause] == 1:
                            break_count[variable] += 1
                            # freebie_move = False
                            # break
                        if score_clauses_auxiliar[variable][clause] == 1:
                            satisfied_total_auxiliar[variable] -= 1
                        score_clauses_auxiliar[variable][clause] -= 1
                        
                        if -variable in variable_clauses: 
                            for clause in variable_clauses[-variable]:
                                if score_clauses_auxiliar[variable][clause] == 0:
                                    satisfied_total_auxiliar[variable] += 1
                                score_clauses_auxiliar[variable][clause] += 1
                    
                for variable in clause_assignment[clause_unsatisfied]:                    
                        
                    if break_count[variable] == 0:
                        variable_flip = variable
                        freebie_move = True
                        break

                if not freebie_move:
                    # With a certain probability, choose a random flip or the best found flip
                    if random.random() <= probability:
                        variable_flip = random.choice(list(break_count.keys()))
                    else:
                        variable_flip = min(break_count, key=lambda k:break_count[k])  
                            
                score_clauses = score_clauses_auxiliar[variable_flip].copy()
                satisfied_total = satisfied_total_auxiliar[variable_flip]
                
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries, flips

        # After all the attempts, if a solution has not been found, return failure
        # satisfied_total = self.get_satisfied_total(satisfied)
        return False, max_tries, max_flips