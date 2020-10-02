from .resources import Rate, _format_name

class Machine:
    def __init__(self, ident, recipies, power):
        self.ident = ident
        self.name = _format_name(ident)
        self.recipies = recipies
        self.power = power

    def __repr__(self):
        return self.ident

    def __str__(self):
        return self.name

class Recipie:
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs

    def __str__(self):
        input_str = ", ".join(str(recipie) for recipie in self.inputs)
        output_str = ", ".join(str(recipie) for recipie in self.outputs)
        return f"[{input_str}] -> [{output_str}]"

    def __repr__(self):
        input_str = ",".join(repr(recipie) for recipie in self.inputs)
        output_str = ",".join(repr(recipie) for recipie in self.outputs)
        return f"{input_str}|{output_str}"

    def to_rates(self):
        return [Rate(rate.resource, -rate.rate) for rate in self.inputs] \
        + [Rate(rate.resource, rate.rate) for rate in self.outputs]
