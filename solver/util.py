def to_from_dict(fields):
    def wrap_the_class(c):
        @classmethod
        def from_dict(cls, d):
            filtered_dict = {
                field: d[field] for field in fields
            }
            return cls(**filtered_dict)

        def to_dict(self):
            return {
                field: self.__dict__[field] for field in fields
            }
        setattr(c, 'from_dict', from_dict)
        setattr(c, 'to_dict', to_dict)
        return c
    return wrap_the_class

