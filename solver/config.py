class AlternateRecipeConfiguration:
    def __init__(self, enabled_recipe_dict):
        self.enabled_recipes = enabled_recipe_dict

    def use_recipe(self, recipe):
        return self.enabled_recipes[recipe]

    def to_dict(self):
        return self.enabled_recipes

    @classmethod
    def from_dict(cls, d):
        return cls(d)
