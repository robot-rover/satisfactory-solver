from genericpath import exists
import json
import yaml
from os import sep, path
import re
import itertools

from solver.resources import ItemRate
from .util import to_from_dict

DOC_JSON_PATH = './Docs.json'


class GameData:
    def __init__(self, items, recipes, machines):
        self.items = items
        self.recipes = recipes
        self.machines = machines

    def to_dict(self):
        return {
            'items': {item.id: item.to_dict() for item in self.items.values()},
            'recipes': {recipe.id: recipe.to_dict() for recipe in self.recipes.values()},
            'machines': {machine.id: machine.to_dict() for machine in self.machines.values()}
        }

    @classmethod
    def from_dict(cls, d):
        return GameData(items={
            id: Item.from_dict(idict) for id, idict in d['items'].items()
        },
            recipes={
            id: Recipe.from_dict(rdict) for id, rdict in d['recipes'].items()
        },
            machines={
            id: Machine.from_dict(mdict) for id, mdict in d['machines'].items()
        })


@to_from_dict(['display', 'id', 'description', 'form', 'icon'])
class Item:
    def __init__(self, display, id, description, form, icon):
        self.display = display
        self.id = id
        self.description = description
        self.form = form
        self.icon = icon

    @classmethod
    def from_node(cls, node):
        display = node["mDisplayName"]
        id = node["ClassName"]
        description = node["mDescription"].replace("\r\n", "\n")
        form = node["mForm"]
        prefix = None
        if form == "RF_SOLID":
            prefix = "icons/Item/"
        elif form == "RF_LIQUID":
            prefix = "icons/Fluid/"
        elif form == "RF_GAS":
            prefix = "icons/Fluid/"
        else:
            raise AssertionError(f"Unknown form {form}")
        icon = prefix + display.replace(" ", "_") + ".png"
        assert path.exists(icon), f"{icon} doesn't exist"
        return cls(display, id, description, form, icon)

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.id


@to_from_dict(["display", "id", "inputs", "outputs", "machine", "duration", 'unlock'])
class Recipe:
    PAR_PAT = re.compile(r"\((.*)\)")
    AMT_PAT = re.compile(r"\(.*?\.(.+?)\"',Amount=(\d+)\)")

    def __init__(self, display, id, inputs, outputs, machine, duration, unlock):
        self.display = display
        self.id = id
        self.inputs = inputs
        self.outputs = outputs
        self.machine = machine
        self.duration = duration
        self.unlock = unlock

    def input_rates(self):
        return [
            ItemRate(resource_id, amount / self.duration) for resource_id, amount in self.inputs.items()
        ]

    def output_rates(self):
        return [
            ItemRate(resource_id, amount / self.duration) for resource_id, amount in self.outputs.items()
        ]

    def get_rates(self):
        return [
            ItemRate(resource_id, -amount / self.duration) for resource_id, amount in self.inputs.items()
        ] + [
            ItemRate(resource_id, amount / self.duration) for resource_id, amount in self.outputs.items()
        ]

    @classmethod
    def from_node(cls, node, machine_set):
        display = node["mDisplayName"]
        id = node["ClassName"]
        inputs = Recipe.parse_item_amount(node["mIngredients"])
        output = Recipe.parse_item_amount(node["mProduct"])
        machines = Recipe.parse_machines(node["mProducedIn"])
        machines = machines if machines is not None else []
        machines = [machine for machine in machines if machine in machine_set]
        assert len(machines) <= 1
        duration = float(node["mManufactoringDuration"]) / 60
        return cls(display, id, inputs, output, machines[0] if len(machines) == 1 else None, duration, None)

    @staticmethod
    def parse_item_amount(str):
        amt_dict = {}
        search_start = 0
        pm = Recipe.PAR_PAT.fullmatch(str)
        assert pm, f"Unrecognized Parenthesis: '{str}'"
        par_str = pm[1]
        while search_start < len(par_str):
            m = Recipe.AMT_PAT.search(par_str, search_start)
            assert m, f"Unrecognized Amount String: '{par_str}'"
            amt_dict[m[1]] = int(m[2])
            search_start = m.end()
        return amt_dict

    @staticmethod
    def parse_machines(str):
        if not str:
            return None
        m = Recipe.PAR_PAT.fullmatch(str)
        assert m, f"Unrecognized Machine String: '{str}'"
        return [machine.split('.')[-1] for machine in m[1].split(',')]

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.id


@to_from_dict(['display', 'id', 'description', 'power', 'icon'])
class Machine:
    def __init__(self, display, id, description, power, icon):
        self.display = display
        self.id = id
        self.description = description
        self.power = power
        self.icon = icon

    @classmethod
    def from_node(cls, node):
        display = node['mDisplayName']
        id = node['ClassName']
        description = node['mDescription'].replace("\r\n", "\n")
        power = float(node['mPowerConsumption'])
        icon = 'icons/Building/' + display.replace(" ", "_") + ".png"
        assert path.exists(icon), f"{icon} doesn't exist"
        return cls(display, id, description, power, icon)

    def __repr__(self):
        return self.ident

    def __str__(self):
        return self.name


def unlock_priority(unlock):
    first = unlock[0]
    priority = 0
    if first == 'MAM Research':
        priority = 3
    elif first == 'Alternate Recipes':
        priority = 4
    elif first == 'Starting Recipes':
        priority = 2
    elif first == 'Starting Recipes':
        priority = 2
    elif first == 'Milestones':
        priority = 1

    return priority


def parse_unlock(node):
    POST_SPLIT_PAT = re.compile(r'\.(.+)\"')
    id = node['ClassName']
    if id == "Schematic_StartingRecipes_C":
        kind = 'EST_Starting'
    elif id == "Schematic_5-1-1_C":
        # Residual Refinery Recipes
        kind = 'EST_Milestone'
    elif id == "Schematic_5-4-1_C":
        # Unpackage Recipes
        kind = 'EST_Milestone'
    else:
        kind = node['mType']
    display = node['mDisplayName']
    tech_tier = node['mTechTier']

    if kind == 'EST_MAM':
        unlock = ('MAM Research',)
    elif kind == 'EST_Alternate':
        unlock = ('Alternate Recipes',)
    elif kind == 'EST_Tutorial':
        unlock = ('Starting Recipes', 'Tutorial')
    elif kind == 'EST_Starting':
        unlock = ('Starting Recipes', 'Initial')
    elif kind == 'EST_Milestone':
        unlock = ('Milestones', f'Tech Tier {tech_tier}', display)
    else:
        unlock = ('Other', kind, id)

    recipe_ids = []
    for unlock_node in node['mUnlocks']:
        if unlock_node['Class'] == 'BP_UnlockRecipe_C':
            remove_paren = Recipe.PAR_PAT.match(unlock_node['mRecipes'])
            assert remove_paren, "Failed to match unlock recipes"
            recipe_paths = remove_paren.group(1).split(',')
            recipe_ids.extend(POST_SPLIT_PAT.search(path).group(1)
                              for path in recipe_paths)

    return (unlock, recipe_ids)


def export_docs(game_data, generate_path='./'):
    with open(generate_path + "game_data.yaml", "w") as data_file:
        print("Generating game_data.yaml")
        yaml.dump(game_data.to_dict(), data_file)


def scrape_docs(doc_path=DOC_JSON_PATH):
    with open(doc_path, "r", encoding="utf16") as file:
        docs = json.load(file)
        docs = {item["NativeClass"]: item["Classes"] for item in docs}

        items = itertools.chain((
            Item.from_node(node)
            for node in docs["Class'/Script/FactoryGame.FGItemDescriptor'"]
        ), (
            Item.from_node(node)
            for node in docs["Class'/Script/FactoryGame.FGResourceDescriptor'"]
        ))
        items = {
            item.id: item for item in items
        }

        machines = (
            Machine.from_node(node) for node in docs["Class'/Script/FactoryGame.FGBuildableManufacturer'"]
        )
        machines = {
            machine.id: machine for machine in machines
        }

        recipes = (
            Recipe.from_node(node, machines) for node in docs["Class'/Script/FactoryGame.FGRecipe'"]
        )
        recipes = {
            recipe.id: recipe for recipe in recipes
        }
        filtered_recipes = {
            recipe_id: recipe for recipe_id, recipe in recipes.items()
            if all(resource in items for resource in recipe.inputs)
            if all(resource in items for resource in recipe.outputs)
            if recipe.machine is not None
        }

        for node in docs["Class'/Script/FactoryGame.FGSchematic'"]:
            unlock, recipe_ids = parse_unlock(node)
            for recipe_id in recipe_ids:
                recipe = filtered_recipes.get(recipe_id)
                if recipe is not None:
                    if recipe.unlock is not None:
                        if recipe.unlock[0] == unlock[0]:
                            continue
                        current_p = unlock_priority(recipe.unlock)
                        new_p = unlock_priority(unlock)
                        assert current_p != new_p, f"Equal Priority, {current_p} == {new_p} for {recipe.display}"
                        if current_p > new_p:
                            continue
                    recipe.unlock = list(unlock)

        return GameData(items, filtered_recipes, machines)


def get_docs(yaml_path="./", doc_path=DOC_JSON_PATH):
    try:
        with open(yaml_path + "game_data.yaml", 'r') as data_stream:
            data = yaml.safe_load(data_stream)
        recipes = {
            recipe["id"]: Recipe.from_dict(recipe) for recipe in data['recipes'].values()
        }
        items = {
            item["id"]: Item.from_dict(item) for item in data['items'].values()
        }
        machines = {
            machine['id']: Machine.from_dict(machine) for machine in data['machines'].values()
        }
        return GameData(items, recipes, machines)

    except FileNotFoundError:
        return scrape_docs(doc_path)


def main(path=DOC_JSON_PATH):
    from sys import argv
    game_data = scrape_docs(path)
    export_docs(game_data)


if __name__ == "__main__":
    main()
