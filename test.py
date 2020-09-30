#!/usr/bin/env python3
import solver
from solver.resources import *

print(solver.machines)

for machine in solver.machines:
    print(machine.name + ': '+ str(machine.recipies))

print(solver.resources)

solver.optimize([Rate(iron_node[1], 2)], reinforced_iron_plate)
