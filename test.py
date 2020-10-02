#!/usr/bin/env python3
import solver
from solver.resources import *

print(solver.machines)

for machine in solver.machines:
    print(machine.name + ': '+ str(machine.recipies))

print(solver.resources)

result = solver.optimize([Rate(iron_node[1], 2)], smart_plating)

print(result)

solver.visualize(result, image_file=f"test.png", dot_file="test.dot")
