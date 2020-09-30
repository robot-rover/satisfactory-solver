from .resources import Node, resources
from .machines import machines

from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

def optimize(capital, target):
    model = LpProblem(name=f"{capital}->{target}", sense=LpMaximize)

    recipies = [(machine, recipie) for machine in machines for recipie in machine.recipies]

    machine_variables = [
        LpVariable(name=f"{{{machine}|{recipie}}}", lowBound=0) for machine,recipie in recipies
    ]

    constraints = {
        resource: [] for resource in resources
    }

    for (machine, recipie), variable in zip(recipies, machine_variables):
        for rate in recipie.to_rates():
            constraints[rate.resource].append(variable * rate.rate)

    for given in capital:
        constraints[given.resource].append(given.rate)

    for resource, terms in constraints.items():
        model += (lpSum(terms) >= 0, f"{resource} Production")
        
    objective = lpSum(constraints[target])

    model += objective

    print(model)

    status = model.solve()
    if status == 1:
        print(f"objective: {model.objective.value()}")
        for var in model.variables():
            if var.value() != 0:
                print(f"{var.name}: {var.value()}")
