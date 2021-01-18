from .resources import Node, Rate

import math

from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable

class Result:
    def __init__(self, target, objective, inputs, recipies, outputs):
        self.target = target
        self.objective = objective
        self.inputs = inputs
        self.recipies = recipies
        self.outputs = outputs

    def __repr__(self):
        return "\n".join([
            f"### {self.target} | {self.objective} ###",
            "--- Inputs ---"
        ] + [
            f"{input}" for input in self.inputs
        ] + [
            "--- Recipies ---"
        ] + [
            f"{machine} - {recipie}: <{quantity}>" for (machine, recipie), quantity in self.recipies.items()
        ] + [
            "--- Outputs ---"
        ] + [
            f"{output}" for output in self.outputs
        ])

def optimize(capital, target, config):
    capital_str = ",".join(repr(rate) for rate in capital)
    model = LpProblem(name=f"[{capital_str}]->{target!r}", sense=LpMaximize)

    recipies = [(machine, recipie) for machine in config.machines for recipie in machine.recipies]

    machine_variables = [
        LpVariable(name=f"{{{machine!r}|{recipie!r}}}", lowBound=0) for machine,recipie in recipies
    ]

    constraint_terms = {
        resource: [] for resource in config.resources.values()
    }

    for (machine, recipie), variable in zip(recipies, machine_variables):
        for rate in recipie.to_rates():
            constraint_terms[rate.resource].append(variable * rate.rate)

    for given in capital:
        constraint_terms[given.resource].append(given.rate)

    objective = lpSum(constraint_terms[target])

    constraints = {
        resource: (lpSum(terms) >= 0, f"{resource!r}_production") for resource, terms in constraint_terms.items()
    }

    for constraint, label in constraints.values():
        model.constraints[label] = constraint

    model.setObjective(objective)

    status = model.solve()
    if status == 1:
        target_production = model.objective.value()
        model.sense = LpMinimize
        power_objective_terms = [
            variable * machine.power for variable, (machine, recipie) in zip(machine_variables, recipies)
        ]
        target_constraint = lpSum(constraint_terms[target]) >= target_production
        model.constraints[f"objective_production_{target!r}"] = target_constraint
        model.setObjective(lpSum(power_objective_terms))
        model.solve()
        model.roundSolution()
        result = Result(target, model.objective.value(), capital, 
        {
            recipie: variable.value() for recipie, variable in zip(recipies, machine_variables)
            if not math.isclose(variable.value(), 0, abs_tol=0.00001)
        },
        [
            Rate(resource, constraint[0].value()) for resource, constraint in constraints.items()
            if not math.isclose(constraint[0].value(), 0, abs_tol=0.00001)
        ])
        return result
