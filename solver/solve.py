from .resources import ItemRate
from .util import to_from_dict

import math

from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable


class Problem:
    def __init__(self, target, inputs):
        self.target = target
        self.inputs = inputs

    def to_dict(self):
        return {
            'target': self.target,
            'inputs': {
                ir.resource: ir.rate for ir in self.inputs
            }
        }

    @classmethod
    def from_dict(cls, d):
        return cls(target=d['target'], inputs=[
            ItemRate(key, val) for key, val in d['inputs'].items()
        ])


class Result:
    def __init__(self, problem, objective, recipes, outputs, throughput):
        self.problem = problem
        self.objective = objective
        self.recipes = recipes
        self.outputs = outputs
        self.throughput = throughput

    def to_dict(self):
        return {
            'problem': self.problem.to_dict(),
            'objective': self.objective,
            'recipes': self.recipes,
            'outputs': {ir.resource: ir.rate for ir in self.outputs}
        }

    def from_dict(cls, d):
        return cls(
            problem=Problem.from_dict(d['problem']),
            objective=d['objective'],
            recipes=d['recipes'],
            outputs=[
                ItemRate(key, val) for key, val in d['outputs'].items()
            ]
        )

    def __repr__(self):
        return "\n".join([
            f"### {self.problem.target} | {self.objective} ###",
            "--- Inputs ---"
        ] + [
            f"{input}" for input in self.problem.inputs
        ] + [
            "--- Recipies ---"
        ] + [
            f"{recipe_id}: <{quantity}>" for recipe_id, quantity in self.recipes.items()
        ] + [
            "--- Outputs ---"
        ] + [
            f"{output}" for output in self.outputs
        ])


def optimize(problem, game_data, recipe_config):

    filtered_recipes = {
        recipe_id: recipe for recipe_id, recipe in game_data.recipes.items()
        if recipe_config.use_recipe(recipe_id)
    }

    capital_str = ",".join(ir.resource for ir in problem.inputs)
    model_name = f'[{capital_str}]->{problem.target}'
    model = LpProblem(name=model_name, sense=LpMaximize)

    recipe_variables = [
        LpVariable(name=f"{recipie_id}", lowBound=0) for recipie_id in filtered_recipes
    ]

    constraint_terms = {
        resource_id: [] for resource_id in game_data.items
    }

    for recipe, variable in zip(filtered_recipes.values(), recipe_variables):
        if all(resource in game_data.items for resource in recipe.inputs) \
                and all(resource in game_data.items for resource in recipe.outputs):
            for item_rate in recipe.get_rates():
                constraint_terms[item_rate.resource].append(
                    variable * item_rate.rate)

    for item_rate in problem.inputs:
        constraint_terms[item_rate.resource].append(item_rate.rate)

    objective = lpSum(constraint_terms[problem.target])

    constraints = {
        resource_id: (lpSum(terms) >= 0, f"{resource_id}_production") for resource_id, terms in constraint_terms.items()
    }

    for constraint, label in constraints.values():
        model.constraints[label] = constraint

    model.setObjective(objective)

    status = model.solve()
    if status == 1:
        target_production = model.objective.value()
        model.sense = LpMinimize
        power_objective_terms = [
            variable * game_data.machines[recipie.machine].power for variable, recipie in zip(recipe_variables, filtered_recipes.values())
        ]
        target_constraint = lpSum(
            constraint_terms[problem.target]) >= target_production
        model.constraints[f"objective_production_{problem.target}"] = target_constraint
        model.setObjective(lpSum(power_objective_terms))
        model.solve()
        throughput = {}
        for ir in problem.inputs:
            throughput[ir.resource] = throughput.get(ir.resource, 0) + ir.rate
        for recipe, variable in zip(filtered_recipes.values(), recipe_variables):
            for ir in recipe.output_rates():
                if variable.value() > 0:
                    throughput[ir.resource] = throughput.get(ir.resource, 0) + ir.rate * variable.value()

        result = Result(problem, model.objective.value(), {
            recipie.id: variable.value() for recipie, variable in zip(filtered_recipes.values(), recipe_variables)
            if not math.isclose(variable.value(), 0, abs_tol=0.00001)
        },
            [
            ItemRate(resource, constraint[0].value()) for resource, constraint in constraints.items()
            if constraint[0].value() is not None
            if not math.isclose(constraint[0].value(), 0, rel_tol=0.00001, abs_tol=0.00001)
        ], throughput)
        return result


def main(args):
    from . import game_parse
    it = iter(args)
    target = next(it)
    inputs = []
    try:
        while True:
            id = next(it)
            rate = int(next(it))
            inputs.append(ItemRate(id, rate))
    except StopIteration:
        pass
    game_data = game_parse.get_docs()
    result = optimize(Problem(target, inputs), game_data)
    print(result)
    return result
