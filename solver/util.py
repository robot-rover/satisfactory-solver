from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from sys import flags

def to_from_dict(fields, manual_fields=[]):
    def wrap_the_class(c):
        @classmethod
        def from_dict(cls, d):
            filtered_dict = {
                field: d[field] for field in fields
            }
            filtered_dict.update({
                field: dc.from_dict(d[field]) for field, dc in manual_fields
            })
            return cls(**filtered_dict)

        def to_dict(self):
            d = {
                field: self.__dict__[field] for field in fields
            }
            d.update({
                field: self.__dict__[field] for field, _ in manual_fields
            })
            return d
        setattr(c, 'from_dict', from_dict)
        setattr(c, 'to_dict', to_dict)
        return c
    return wrap_the_class

class AttributeEncoder(JSONEncoder):
    def default(self, o):
        return o.to_dict()

@to_from_dict(['name', 'args', 'flags'])
class Case:
    def __init__(self, name, args, flags=[]):
        self.name = name
        self.args = args
        self.flags = flags

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Case({self.name}, {self.args})'

