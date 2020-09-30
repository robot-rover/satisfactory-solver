from .resources import Node, resources
from .machines import machines

from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

def optimize(capital, target):
    model = LpProblem(name=f"{capital}->{target}", sense=LpMaximize)

    recipies = [(machine, recipie) for machine in machines for recipie in machine.recipies]

    machine_variables = [
        LpVariable(name=f"{{{machine}|{recipie}}}", lowBound=0) for machine,recipie in recipies
    ]

    objective = None

    for resource in resources:
        terms = []
        for (machine, recipie), variable in zip(recipies, machine_variables):
            for input in recipie.inputs:
                if input.resource == resource:
                    terms.append(variable * -input.rate)
            for output in recipie.outputs:
                if output.resource == resource:
                    terms.append(variable * output.rate)

        for given in capital:
            if given.resource == resource:
                terms.append(given.rate)

        if resource == target:
            objective = lpSum(terms)        
        model += (lpSum(terms) >= 0, f"{resource} Production")

    model += objective

    print(model)

    status = model.solve()
    if status == 1:
        print(f"objective: {model.objective.value()}")
        for var in model.variables():
            if var.value() != 0:
                print(f"{var.name}: {var.value()}")
