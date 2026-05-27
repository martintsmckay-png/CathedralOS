class SystemMapper:
    def __init__(self):
        self.entities = {}

    def register(self, entity_id, data):
        self.entities[entity_id] = data

    def visualize(self):
        return "nestedcontainmenttree_generated"
