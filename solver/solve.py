from .resources import ItemRate

import math

from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable
def recipe_to_rates(recipe):
    return [ItemRate(resource, -rate) for resource, rate in recipe.inputs.items()] \
    + [ItemRate(resource, rate) for resource, rate in recipe.outputs.items()]

class Problem:
    def __init__(self, target, inputs):
        self.target = target
        self.inputs = inputs

class Result:
    def __init__(self, problem, objective, recipes, outputs):
        self.problem = problem
        self.objective = objective
        self.recipes = recipes
        self.outputs = outputs

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

def optimize(problem, game_data):
    filtered_recipes = {
        recipe_id: recipe for recipe_id, recipe in game_data.recipes.items()
        if all(resource in game_data.items for resource in recipe.inputs)
        if all(resource in game_data.items for resource in recipe.outputs)
        if recipe.machine is not None
    }

    # for recipe in game_data.recipes.values():
    #     print(f'{recipe.id} @ {recipe.machine}: {recipe.inputs} | {recipe.outputs}')

    capital_str = ",".join(ir.resource for ir in problem.inputs)
    model_name = f'[{capital_str}]->{problem.target}'
    print(model_name)
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
            for item_rate in recipe_to_rates(recipe):
                constraint_terms[item_rate.resource].append(variable * item_rate.rate)

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
        target_constraint = lpSum(constraint_terms[problem.target]) >= target_production
        model.constraints[f"objective_production_{problem.target}"] = target_constraint
        model.setObjective(lpSum(power_objective_terms))
        model.solve()
        model.roundSolution()
        result = Result(problem, model.objective.value(), {
            recipie.id: variable.value() for recipie, variable in zip(filtered_recipes.values(), recipe_variables)
            if not math.isclose(variable.value(), 0, abs_tol=0.00001)
        },
        [
            ItemRate(resource, constraint[0].value()) for resource, constraint in constraints.items()
            if not math.isclose(constraint[0].value(), 0, abs_tol=0.00001)
        ])
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
