from .resources import Node, resources, Rate
from .machines import machines

import math

from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

class Result:
    def __init__(self, target, inputs, recipies, outputs):
        self.target = target
        self.inputs = inputs
        self.recipies = recipies
        self.outputs = outputs

    def __repr__(self):
        return "\n".join([
            f"### {self.target} ###",
            "--- Inputs ---"
        ] + [
            f"{input}" for input in self.inputs
        ] + [
            "--- Recipies ---"
        ] + [
            f"{recipie}: {quantity}" for recipie, quantity in self.recipies
        ] + [
            "--- Outputs ---"
        ] + [
            f"{output}" for output in self.outputs
        ])

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

    objective = lpSum(constraints[target])

    constraints = {
        resource: (lpSum(terms) >= 0, f"{resource} Production") for resource, terms in constraints.items()
    }

    for constraint in constraints.values():
        model += constraint

    model += objective

    status = model.solve()
    if status == 1:
        result = Result(target, capital, 
        [
            (recipie, variable.value()) for recipie, variable in zip(recipies, machine_variables)
            if not math.isclose(variable.value(), 0, abs_tol=0.00001)
        ],
        [
            Rate(resource, constraint[0].value()) for resource, constraint in constraints.items()
            if not math.isclose(constraint[0].value(), 0, abs_tol=0.00001)
        ])
        return result


