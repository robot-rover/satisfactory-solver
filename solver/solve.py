from .resources import Node
from .machines import machines

from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

def produces_list(target):
    result = []
    for machine in machines:
        for index, recipie in enumerate(machine.recipies):
            if recipie.output.get_resource() == target:
                result.append((machine, recipie))
    return result

class ProductionNode:
    def __init__(self, target, subnodes):
        self.target = target
        self.subnodes = subnodes

    def print(self, indent):
        for node in self.subnodes:
            node.print(indent + 1)

class CapitalNode(ProductionNode):
    def __init__(self, target):
        super().__init__(target, [])

    def print(self, indent):
        print(("  " * indent) + f"{self.target} <INPUT>")
        super().print(indent)

class MachineNode(ProductionNode):
    def __init__(self, target, subnodes, machine, recipie):
        super().__init__(target, subnodes)
        self.machine = machine
        self.recipie = recipie

    def print(self, indent):
        print(("  " * indent) + f"{self.machine} | {self.recipie.inputs} -> {self.recipie.output}")
        super().print(indent)

def production_list(capital, target, stack):
    print(target, capital)
    stack_size = len(stack)
    branch_options = produces_list(target)
    if target in (rate.get_resource() for rate in capital):
        return True
    if target in (recipie[1].output.get_resource() for recipie in stack):
        return True
    for option in branch_options:
        try:
            subnodes = []
            for ingredient in option[1].inputs:
                if not production_list(capital, ingredient.get_resource(), stack):
                    raise StopIteration
            stack.append(option)
            return True
        except StopIteration:
            pass

    del stack[stack_size:]

    return False

def optimize(capital, target, stack):
    model = LpProblem(name=f"{capital}->{target}", sense=LpMaximize)

    machine_variables = [
        LpVariable(name=f"{{{recipie[0]}|{recipie[1]}}}", lowBound=0) for recipie in stack
    ]

    for recipie, variable in zip(stack, machine_variables):
        producing = recipie[1].output.get_resource()
        require = [
            (variable, input.rate) for recipie, variable in zip(stack, machine_variables)
            for input in recipie[1].inputs
            if producing == input.get_resource()
        ]
        require_eq = [
            variable * -rate for variable, rate in require
        ]
        require_eq.append(variable * recipie[1].output.rate)
        model += (lpSum(require_eq) >= 0, f"{recipie[1].output.get_resource()} Production")

    for rate in capital:
        producing = rate.get_resource()
        require = [
            (variable, input.rate) for recipie, variable in zip(stack, machine_variables)
            for input in recipie[1].inputs
            if producing == input.get_resource()
        ]
        require_eq = [
            variable * rate for variable, rate in require
        ]
        model += (lpSum(require_eq) <= rate.rate, f"Input of {rate}")

    obj_func = machine_variables[-1]
    model += obj_func

    print(model)

    status = model.solve()
    if status == 1:
        print(f"objective: {model.objective.value()}")
        for var in model.variables():
            print(f"{var.name}: {var.value()}")
