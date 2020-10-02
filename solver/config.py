import yaml

from .resources import Node, Resource, Rate
from .machines import Machine, Recipie

def ratetup(dct, resource_fn):
    return [
        Rate(resource_fn(resource), rate) for resource, rate in dct.items()
    ]


class Config:
    def __init__(self, yml):
        resource_names = yml['node_resources'] + yml['resources']

        self.resources = {
            name: Resource(name) for name in resource_names
        }

        self.nodes = {
            name: Node.make(self.resources[name]) for name in yml['node_resources']
        }

        node_resources = {
            repr(node): node for node_type in self.nodes.values() for node in node_type
        }

        self.resources.update(node_resources)

        resource_fn = lambda name: self.resources[name]

        self.machines = [
            Machine(name, [
                Recipie(ratetup(recipie['inputs'], resource_fn), ratetup(recipie['outputs'], resource_fn)) for recipie in data['recipies']
            ], data['power'])
            for name, data in yml['machines'].items()
        ]

        miners = [
            Machine(name, [
                Recipie([Rate(node, 1)], [Rate(node.resource, node.purity_adjust(data['rate']))]) for node_type in self.nodes.values() for node in node_type
            ], data['power'])
            for name, data in yml['miners'].items()
        ]

        self.machines.extend(miners)
    
    def __repr__(self):
        return f"Config\nResources: {self.resources.values()}\nNodes: {self.nodes.keys()}\nMachines: {self.machines}"

class Factory:
    def __init__(self, name, inputs, target):
        self.name = name
        self.inputs = inputs
        self.target = target

    @classmethod
    def from_yml(cls, yml, config):
        return [
            Factory(factory_name,
                [
                    Rate(config.resources[name], rate) for name, rate in data['inputs'].items()
                ], 
                config.resources[data['target']]
            ) for factory_name, data in yml.items()
        ]

def load_config(filename):
    with open(filename) as file:
        yml = yaml.load(file, Loader=yaml.SafeLoader)
        return Config(yml)

def load_factory(filename):
    with open(filename) as file:
        yml = yaml.load(file, Loader=yaml.SafeLoader)
        config = load_config(yml['config'])
        factories = Factory.from_yml(yml['factories'], config)
        return (config, factories)
