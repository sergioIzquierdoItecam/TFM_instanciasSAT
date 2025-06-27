import ast

def load_assignment(file_path):
    """Carga el archivo de asignación y convierte el contenido a un diccionario."""
    with open(file_path, 'r') as f:
        return ast.literal_eval(f.read())

def load_formula(file_path):
    """Carga la fórmula CNF del archivo y la convierte en una lista de cláusulas."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # Ignorar líneas vacías, comentarios y encabezado
    clauses = [
        list(map(int, line.strip().split()[:-1]))
        for line in lines if line.strip() and not line.startswith('c') and not line.startswith('p')
    ]
    return clauses

def is_clause_satisfied(clause, assignment):
    """Verifica si una cláusula está satisfecha según la asignación dada."""
    for literal in clause:
        var = abs(literal)
        value = assignment.get(var, None)
        if value is not None:
            if (literal > 0 and value) or (literal < 0 and not value):
                return True
    return False

def is_formula_satisfied(clauses, assignment):
    """Verifica si la fórmula está satisfecha."""
    return all(is_clause_satisfied(clause, assignment) for clause in clauses)

def main():
    assignment_file = "random_assignment.txt"
    formula_file = "community_formula.txt"
    
    # Cargar los datos
    assignment = load_assignment(assignment_file)
    clauses = load_formula(formula_file)
    
    # Verificar la fórmula
    if is_formula_satisfied(clauses, assignment):
        print("La asignación satisface la fórmula CNF.")
    else:
        print("La asignación NO satisface la fórmula CNF.")

if __name__ == "__main__":
    main()
