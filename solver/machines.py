from .resources import *

class Machine:
    def __init__(self, name, recipies, power):
        self.name = name
        self.recipies = recipies
        self.power = power

    def __repr__(self):
        return f"{self.name}"

class Miner(Machine):
    @classmethod
    def make(cls, name, rate, power, node_map):
        recipies = [
            Recipie([Rate(node, 1)], Rate(node.resource, node.purity_adjust(rate))) for node_type in node_map.values() for node in node_type
        ]
        return cls(name, recipies, power)

class Recipie:
    def __init__(self, inputs, output):
        self.inputs = inputs
        self.output = output

    def __repr__(self):
        return f"{self.inputs} -> {self.output}"

miner_mk1 = Miner.make("Miner Mk.1", 60, 5, nodes)

smelter = Machine("Smelter", [
    Recipie([Rate(copper_ore, 30)], Rate(copper_ingot, 30)),
    Recipie([Rate(iron_ore, 30)], Rate(iron_ingot, 30))
], 4)

constructor = Machine("Constructor", [
    Recipie([Rate(iron_ingot, 30)], Rate(iron_plate, 20)),
    Recipie([Rate(iron_ingot, 15)], Rate(iron_rod, 15)),
    Recipie([Rate(copper_ingot, 15)], Rate(wire, 30)),
    Recipie([Rate(wire, 60)], Rate(cable, 30)),
    Recipie([Rate(iron_rod, 10)], Rate(screw, 40))
], 4)

assembler = Machine("Assembler", [
    Recipie([Rate(iron_rod, 20), Rate(screw, 100)], Rate(rotor, 4)),
    Recipie([Rate(iron_plate, 30), Rate(screw, 60)], Rate(reinforced_iron_plate, 5)),
    Recipie([Rate(reinforced_iron_plate, 2), Rate(rotor, 2)], Rate(smart_plating, 2))
], 15)

machines = [miner_mk1, smelter, constructor, assembler]
