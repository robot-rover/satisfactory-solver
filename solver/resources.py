def _format_name(snake_case):
    words = snake_case.split('_')
    return " ".join(word.capitalize() for word in words)

class Resource:
    def __init__(self, ident):
        self.name = _format_name(ident)
        self.ident = ident

    def __repr__(self):
        return self.ident

    def __str__(self):
        return self.name

class Rate:
    def __init__(self, resource, rate):
        self.resource = resource
        self.rate = rate

    def __str__(self):
        return f"{self.resource} @ {self.rate}/min"

    def __repr__(self):
        return f"{self.resource!r}_{self.rate}"

    def get_resource(self):
        return self.resource

class Node:
    _purity_str = [
        "impure",
        "normal",
        "pure"
    ]

    def __init__(self, resource, purity):
        self.resource = resource
        self.purity = purity

    def __repr__(self):
        purity_str = Node._purity_str[self.purity]
        return f"{self.resource!r}_node_{purity_str}"

    def __str__(self):
        purity_str = Node._purity_str[self.purity].capitalize()
        return f"{purity_str} {self.resource} Node {purity_str}"

    def purity_adjust(self, rate):
        if self.purity == 0:
            return rate // 2
        if self.purity == 2:
            return rate * 2
        return rate

    @classmethod
    def make(cls, resource):
        return [cls(resource, purity) for purity in range(0,3)]
