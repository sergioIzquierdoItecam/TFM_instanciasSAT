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
        path_generator_model = "./communityAttachment/random"
        # Arguments for the random model generator
        arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                     '-k', str(self.clauseLength), '-s', str(self.seed)]

        # Create a subprocess to run the model generator and capture its output
        process = subprocess.Popen([path_generator_model] + arguments, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        decoded_output = output.decode("utf-8")
        # Convert the output into a list of clauses, each represented as a list of integers
        formula = [[int(value) for value in line.split()[:-1]] for line in decoded_output.splitlines()[6:]]
        return formula

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

    # Count how many clauses are satisfied in total
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to solve the SAT problem using a max flips and max tries approach
    def solve(self, max_flips, max_tries):
        
        for tries in range(max_tries):
            # Random initial assignment
            # random.seed(0)
            assignment = {variable+1: random.choice([True, False]) for variable in range(self.variables)}
            variable_clauses,score_clauses = self.get_variable_clauses(assignment) 

            for flips in range(max_flips):
                               
                satisfied_total = 0 
                for clauses in score_clauses:
                    if score_clauses[clauses] != 0:
                        satisfied_total += 1
                if satisfied_total == self.clauses:  # If all clauses are satisfied
                    return True, tries+1, flips+1            
            
                break_count_min = self.clauses
                score_clauses_auxiliar = score_clauses.copy()
                
                for variable in range(1,self.variables+1):
                    satisfied_total_auxiliar = satisfied_total
                    # if variable is true and score clause is 1, one less satisfied clause
                    if variable in variable_clauses: 
                        for clause in variable_clauses[variable]:
                            if score_clauses_auxiliar[clause] == 1:
                                satisfied_total_auxiliar -= 1
                            score_clauses_auxiliar[clause] -= 1 
                    # if variable is false and score clause is 0, one more satisfied clause
                    if -variable in variable_clauses: 
                        for clause in variable_clauses[-variable]:
                            if score_clauses_auxiliar[clause] == 0:
                                satisfied_total_auxiliar += 1
                            score_clauses_auxiliar[clause] += 1          
                                          
                    break_count = self.clauses - satisfied_total_auxiliar

                    if satisfied_total_auxiliar == self.clauses:
                        return True, tries+1, flips+1
                    elif break_count < break_count_min:
                        break_count_min = break_count
                        score_clauses_min = score_clauses_auxiliar.copy()

                score_clauses = score_clauses_min.copy()
        
        # Return the final result after all tries and flips
        return False, max_tries, max_flips
