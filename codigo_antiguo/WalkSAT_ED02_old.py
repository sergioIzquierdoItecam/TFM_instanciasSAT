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
    def get_variable_clauses(self):
        variable_clauses = {}
        for clause_index, clause in enumerate(self.formula, start=1):
            for literal in clause:
                variable = literal        
                if variable not in variable_clauses:
                    variable_clauses[variable] = []
                variable_clauses[variable].append(clause_index)
        return variable_clauses
    
    def get_score_clauses(self, assignment):
        score_clauses = {}
        for clause_index, clause in enumerate(self.formula, start=1):
            for literal in clause:
                variable = literal
                if clause_index not in score_clauses:
                    score_clauses[clause_index] = 0
                if (variable > 0 and assignment[abs(variable)]) or (variable < 0 and not(assignment[abs(variable)])):
                    score_clauses[clause_index] += 1
        return score_clauses

    # Calculates the total number of clauses that are satisfied
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to attempt solving the SAT problem, allowing flips and retries
    def solve(self, max_flips, max_tries, probability):
        variable_clauses = self.get_variable_clauses()  # Get the mapping from variables to clauses
        satisfied = {clause + 1: False for clause in range(self.clauses)}  # Initialize all clauses as unsatisfied
        
        n_variable_clauses = 0
        
        for tries in range(max_tries):
            # Randomly assign True/False to each variable
            assignment = {variable + 1: random.choice([True, False]) for variable in range(self.variables)}
            score_clauses = self.get_score_clauses(assignment)            

            for flips in range(max_flips):
                satisfied_total = 0 
                for clauses in score_clauses:
                    if score_clauses[clauses] != 0:
                        satisfied_total += 1
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries, flips                
                
                clauses_satisfied = [key for key, value in score_clauses.items() if value>0]
                clauses_unsatisfied = [key for key, value in score_clauses.items() if value==0]
                clause_unsatisfied = random.choice(clauses_unsatisfied)
                
                freebie_move = True
                
                break_count_min = self.clauses
                
                for variable in self.formula[clause_unsatisfied - 1]:
                    score_clauses_auxiliar = score_clauses.copy()
                    satisfied_total_auxiliar = satisfied_total
                    if (variable > 0 and assignment[abs(variable)]) or (variable < 0 and not(assignment[abs(variable)])):
                        for clause in variable_clauses[variable]:
                            if score_clause[clause] == 1:
                                freebie_move = False
                                break
                            score_clause = score_clauses[clause]
                            if variable > 0 and score_clause == 1:
                                score_clauses_auxiliar[clause] -= 1
                                satisfied_total_auxiliar -= 1
                            elif variable < 0 and score_clause == 0:
                                score_clauses_auxiliar[clause] += 1
                                satisfied_total_auxiliar += 1
                                        
                    # variable = abs(variable)
                    # satisfied_auxiliar = satisfied.copy()
                    # assignment_auxiliar = assignment.copy()
                    # assignment_auxiliar[variable] = not assignment_auxiliar[variable]
                    
                    # # Get the variables's satisfied clauses 
                    # clauses_satisfied_variable = [clause for clause in variable_clauses[variable] if clause in clauses_satisfied] 
                    
                    # n_variable_clauses += len(clauses_satisfied_variable)
                    # satisfied_auxiliar = self.evaluate_formula(assignment_auxiliar, satisfied_auxiliar, clauses_satisfied_variable)
                    # satisfied_total_auxiliar = self.get_satisfied_total(satisfied_auxiliar)   
                    
                    break_count = satisfied_total - satisfied_total_auxiliar
                    
                    if satisfied_total_auxiliar == self.clauses:
                        return True, tries, flips, n_variable_clauses
                    # If flipping improves or maintains satisfaction, flip the variable
                    if break_count <= 0:
                        score_clauses = score_clauses_auxiliar.copy()
                        freebie_move = True
                        break
                    elif break_count < break_count_min:
                        break_count_min = break_count
                        score_clauses_min = score_clauses_auxiliar.copy()
                # After evaluating all variables in the unsatisfied clause
                if not freebie_move:
                    # With a certain probability, choose a random flip or the best found flip
                    if random.random() <= probability:
                        variable = random.choice(self.formula[clause_unsatisfied - 1])
                        if assignment[abs(variable)]:                            
                            for clause in variable_clauses[variable]:
                                score_clause = score_clauses[clause]
                                if variable > 0 and score_clause == 1:
                                    score_clauses[clause] -= 1
                                    satisfied_total -= 1
                                elif variable < 0 and score_clause == 0:
                                    score_clauses[clause] += 1
                                    satisfied_total += 1
                    else:
                        score_clauses = score_clauses_min.copy()
        
        # After all the attempts, if a solution has not been found, return failure
        # satisfied_total = self.get_satisfied_total(satisfied)
        return False, max_tries, max_flips, n_variable_clauses