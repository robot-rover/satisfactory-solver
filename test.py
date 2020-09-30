#!/bin/python3
import solver
from solver.resources import copper_node, cable, iron_node, smart_plating, Rate

print(solver.machines)

for machine in solver.machines:
    print(machine.name + ': '+ str(machine.recipies))

lst = []
tree = solver.production_list([Rate(copper_node[1], 1)], cable, lst)
assert(tree)

print()
print("\n".join(repr(item) for item in lst))

lst = []
tree = solver.production_list([Rate(iron_node[1], 2)], smart_plating, lst)
assert(tree)

print()
print("\n".join(repr(item) for item in lst))

solver.optimize([Rate(iron_node[1], 2)], smart_plating, lst)