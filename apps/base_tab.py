class Tab:
    def __init__(self, name):
        self.name = name

    def execute(self):
        raise NotImplementedError("Method not implemented by subclass")