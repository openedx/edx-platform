class completion(object):
    def __init__(self, d=None):
        self.dict = dict()
        if d: 
            self.dict.update(d)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __add__(self, other):
        result = dict()
        dict.update(self.dict)
        dict.update(other.dict)

    def __contains__(self, key):
        pass
