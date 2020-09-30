#!/bin/python3
import solver
from solver.resources import copper_node, cable, iron_node, smart_plating, Rate

print(solver.machines)

for machine in solver.machines:
    print(machine.name + ': '+ str(machine.recipies))

solver.optimize([Rate(iron_node[1], 2)], smart_plating)