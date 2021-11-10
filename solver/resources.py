class ItemRate:
    def __init__(self, resource, rate):
        assert isinstance(resource, str)
        self.resource = resource
        self.rate = rate

    def format(self, game_data):
        return f"{game_data.items[self.resource].display} @ {round(float(self.rate), 3)}/min"

    def __repr__(self):
        return f"{self.resource!r}_{self.rate}"
