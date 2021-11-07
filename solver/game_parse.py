from genericpath import exists
import json
import yaml
from os import sep, path
import re
from .util import to_from_dict

class GameData:
    def __init__(self, items, recipes, machines):
        self.items = items
        self.recipes = recipes
        self.machines = machines

DOCS_JSON_OPTIONS = [
    "./Docs.json",
    "%steamapps%/common/Satisfactory/CommunityResources/Docs/Docs.json",
    "C://Program Files (x86)/Steam/steamapps/common/Satisfactory/CommunityResources/Docs/Docs.json",
    "E://SteamLibrary/steamapps/common/Satisfactory/CommunityResources/Docs/Docs.json",
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/Satisfactory/CommunityResources/Docs/Docs.json",
    "/mnt/e/SteamLibrary/steamapps/common/Satisfactory/CommunityResources/Docs/Docs.json"
]


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


@to_from_dict(["display", "id", "inputs", "outputs", "machine"])
class Recipe:
    PAR_PAT = re.compile(r"\((.*)\)")
    AMT_PAT = re.compile(r"\(.*?\.(.+?)\"',Amount=(\d+)\)")

    def __init__(self, display, id, inputs, outputs, machine):
        self.display = display
        self.id = id
        self.inputs = inputs
        self.outputs = outputs
        self.machine = machine

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
        return cls(display, id, inputs, output, machines[0] if len(machines) == 1 else None)

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


def scrape_docs(generate_path="./", doc_path=None):
    if doc_path is None:
        try:
            doc_path = next(p for p in DOCS_JSON_OPTIONS if path.exists(p))
        except StopIteration:
            raise RuntimeError("No Satisfactory Configuration Found!")
    with open(doc_path, "r", encoding="utf16") as file:
        docs = json.load(file)
        docs = {item["NativeClass"]: item["Classes"] for item in docs}

    with open(generate_path + "game_data.yaml", "w") as data_file:
        print("Generating game_data.yaml")

        items = [
            Item.from_node(node).to_dict()
            for node in docs["Class'/Script/FactoryGame.FGItemDescriptor'"]
        ] + [
            Item.from_node(node).to_dict()
            for node in docs["Class'/Script/FactoryGame.FGResourceDescriptor'"]
        ]

        machines = [
            Machine.from_node(node).to_dict() for node in docs["Class'/Script/FactoryGame.FGBuildableManufacturer'"]
        ]

        machine_set = set(machine['id'] for machine in machines)

        recipes = [
            Recipe.from_node(node, machine_set).to_dict() for node in docs["Class'/Script/FactoryGame.FGRecipe'"]
        ]

        game_data = {
            'items': items,
            'recipes': recipes,
            'machines': machines
        }

        yaml.dump(game_data, data_file)


def get_docs(yaml_path="./", doc_path=None):
    def parse_items():
        with open(yaml_path + "game_data.yaml", 'r') as data_stream:
            data = yaml.safe_load(data_stream)
        recipes = {
            recipe["id"]: Recipe.from_dict(recipe) for recipe in data['recipes']
        }
        items = {
            item["id"]: Item.from_dict(item) for item in data['items']
        }
        machines = {
            machine['id']: Machine.from_dict(machine) for machine in data['machines']
        }
        return GameData(items, recipes, machines)

    try:
        return parse_items()
    except FileNotFoundError:
        if doc_path:
            scrape_docs(yaml_path, doc_path)
        else:
            scrape_docs(yaml_path)
        return parse_items()


def main(path=None):
    from sys import argv
    scrape_docs('./', path)


if __name__ == "__main__":
    main()
