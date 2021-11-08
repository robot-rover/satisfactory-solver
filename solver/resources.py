def _format_name(snake_case):
    words = snake_case.split('_')
    return " ".join(word.capitalize() for word in words)

class ItemRate:
    def __init__(self, resource, rate):
        assert isinstance(resource, str)
        self.resource = resource
        self.rate = rate

    def format(self, game_data):
        return f"{game_data.items[self.resource].display} @ {self.rate}/min"

    def __repr__(self):
        return f"{self.resource!r}_{self.rate}"
