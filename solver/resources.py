class Resource:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}"

class Rate:
    def __init__(self, resource, rate):
        self.resource = resource
        self.rate = rate

    def __repr__(self):
        return f"{self.resource} @ {self.rate}/min"

    def get_resource(self):
        return self.resource

class Node:
    _purity_str = [
        "Impure",
        "Normal",
        "Pure"
    ]

    def __init__(self, resource, purity):
        self.resource = resource
        self.purity = purity

    def __repr__(self):
        purity_str = Node._purity_str[self.purity]
        return f"{purity_str} {self.resource} Node"

    @classmethod
    def make(cls, resource):
        return [cls(resource, purity) for purity in range(0,3)]

iron_ore = Resource("Iron Ore")
copper_ore = Resource("Copper Ore")
limestone = Resource("Limestone")

iron_ingot = Resource("Iron Ingot")
copper_ingot = Resource("Copper Ingot")

resources = [iron_ore, copper_ore, limestone, iron_ingot, copper_ingot]

iron_plate = Resource("Iron Plate")
iron_rod = Resource("Iron Rod")
wire = Resource("Wire")
cable = Resource("Cable")
screw = Resource("Screw")

rotor = Resource("Rotor")
reinforced_iron_plate = Resource("Reinforced Iron Plate")
smart_plating = Resource("Smart Plating")

iron_node = Node.make(iron_ore)
copper_node = Node.make(copper_ore)
limestone_node = Node.make(limestone)


nodes_nested = [iron_node, copper_node, limestone_node]
nodes = {nodes[0].resource: nodes for nodes in nodes_nested}