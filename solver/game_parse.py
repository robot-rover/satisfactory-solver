from genericpath import exists
import json
import yaml
from os import sep, path
import re

DOCS_JSON = "/mnt/e/SteamLibrary/steamapps/common/Satisfactory/CommunityResources/Docs/Docs.json"


class Item:
    def __init__(self, node):
        self.display = node["mDisplayName"]
        self.id = node["ClassName"]
        self.description = node["mDescription"].replace("\r\n", "\n")
        self.form = node["mForm"]
        prefix = None
        if self.form == "RF_SOLID":
            prefix = "icons/Item/"
        elif self.form == "RF_LIQUID":
            prefix = "icons/Fluid/"
        else:
            raise AssertionError(f"Unknown form {self.form}")
        self.icon = prefix + self.display.replace(" ", "_") + ".png"
        assert path.exists(self.icon), f"{self.icon} doesn't exist"

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.id

    def to_dict(self):
        return {
            "display": self.display,
            "id": self.id,
            "description": self.description,
            "icon": self.icon,
        }


class Recipe:
    PAR_PAT = re.compile(r"\((.*)\)")
    AMT_PAT = re.compile(r"\(.*?\.(.+?)\"',Amount=(\d+)\)")

    def __init__(self, node):
        self.display = node["mDisplayName"]
        self.id = node["ClassName"]
        self.inputs = Recipe.parse_item_amount(node["mIngredients"])
        self.output = Recipe.parse_item_amount(node["mProduct"])
        self.machine = Recipe.parse_machine(node["mProducedIn"])

    @staticmethod
    def parse_item_amount(str):
        amt_dict = {}
        search_start = 0
        pm = Recipe.PAR_PAT.fullmatch(str)
        assert pm, f"Unrecognized Parenthesizaton: '{str}'"
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

    def to_dict(self):
        return {
            "display": self.display,
            "id": self.id,
            "inputs": self.inputs,
            "output": self.output,
            "machine": self.machine,
        }


def parse_docs(path):
    with open(path, "r", encoding="utf16") as file:
        docs = json.load(file)
        docs = {item["NativeClass"]: item["Classes"] for item in docs}

    try:
        with open("items.yaml", "x") as items_config:
            print("Generating items.yaml")
            items = [
                Item(node)
                for node in docs["Class'/Script/FactoryGame.FGItemDescriptor'"]
            ]
            yaml.dump([item.to_dict() for item in items], items_config)
    except FileExistsError:
        print("items.yaml exists, skipping...")

    try:
        with open("recipes.yaml", "x") as recipe_config:
            print("Generating recipes.yaml")
            recipes = [
                Recipe(node) for node in docs["Class'/Script/FactoryGame.FGRecipe'"]
            ]
            yaml.dump([recipe.to_dict() for recipe in recipes], recipe_config)
    except FileExistsError:
        print("recipes.yaml already exists, skipping...")


parse_docs(DOCS_JSON)
