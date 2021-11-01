from genericpath import exists
import json
import yaml
from os import sep, path
import re
from .util import to_from_dict

DOCS_JSON_OPTIONS = [
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
        else:
            raise AssertionError(f"Unknown form {form}")
        icon = prefix + display.replace(" ", "_") + ".png"
        assert path.exists(icon), f"{icon} doesn't exist"
        return cls(display, id, description, form, icon)

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.id

@to_from_dict(["display", "id", "inputs", "output", "machine"])
class Recipe:
    PAR_PAT = re.compile(r"\((.*)\)")
    AMT_PAT = re.compile(r"\(.*?\.(.+?)\"',Amount=(\d+)\)")

    def __init__(self, display, id, inputs, output, machine):
        self.display = display
        self.id = id
        self.inputs = inputs
        self.output = output
        self.machine = machine

    @classmethod
    def from_node(cls, node):
        display = node["mDisplayName"]
        id = node["ClassName"]
        inputs = Recipe.parse_item_amount(node["mIngredients"])
        output = Recipe.parse_item_amount(node["mProduct"])
        machine = Recipe.parse_machine(node["mProducedIn"])
        return cls(display, id, inputs, output, machine)

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
    def parse_machine(str):
        if not str:
            return None
        m = Recipe.PAR_PAT.fullmatch(str)
        assert m, f"Unrecognized Machine String: '{str}'"
        return m[1].split(".")[-1]

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.id

def scrape_docs(generate_path="./", doc_path=None):
    if doc_path is None:
        try:
            doc_path = next(p for p in DOCS_JSON_OPTIONS if path.exists(p))
        except StopIteration:
            raise RuntimeError("No Satisfactory Configuration Found!")
    with open(doc_path, "r", encoding="utf16") as file:
        docs = json.load(file)
        docs = {item["NativeClass"]: item["Classes"] for item in docs}

    try:
        with open(generate_path + "items.yaml", "x") as items_config:
            print("Generating items.yaml")
            items = [
                Item.from_node(node)
                for node in docs["Class'/Script/FactoryGame.FGItemDescriptor'"]
            ]
            yaml.dump([item.to_dict() for item in items], items_config)
    except FileExistsError:
        print("items.yaml exists, skipping...")

    try:
        with open(generate_path + "recipes.yaml", "x") as recipe_config:
            print("Generating recipes.yaml")
            recipes = [
                Recipe.from_node(node) for node in docs["Class'/Script/FactoryGame.FGRecipe'"]
            ]
            yaml.dump([recipe.to_dict() for recipe in recipes], recipe_config)
    except FileExistsError:
        print("recipes.yaml already exists, skipping...")

def get_docs(yaml_path = "./", doc_path = None):
    def parse_items():
        with open(yaml_path + "recipes.yaml", 'r') as recipe_stream:
            recipes = yaml.safe_load(recipe_stream)
        with open(yaml_path + "items.yaml", 'r') as item_stream:
            items = yaml.safe_load(item_stream)
        recipes = {
            recipe["id"]: Recipe.from_dict(recipe) for recipe in recipes
        }
        items = {
            item["id"]: Item.from_dict(item) for item in items
        }
        return (recipes, items)

    try:
        return parse_items()
    except FileNotFoundError:
        if doc_path:
            scrape_docs(yaml_path, doc_path)
        else:
            scrape_docs(yaml_path)
        return parse_items()


def main():
    from sys import argv
    scrape_docs(doc_path=(argv[1] if len(argv) > 1 else None))

if __name__ == "__main__":
    main()
