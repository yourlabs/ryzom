class Methods():
    methods = {}

    @classmethod
    def add(cls, methods):
        cls.methods.update(methods)

    @classmethod
    def get(cls, name):
        return cls.methods.get(name, None)
