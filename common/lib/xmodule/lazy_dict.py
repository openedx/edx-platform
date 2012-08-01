from collections import MutableMapping

class LazyLoadingDict(MutableMapping):
    """
    A dictionary object that lazily loads its contents from a provided
    function on reads (of members that haven't already been set).
    """

    def __init__(self, loader):
        '''
        On the first read from this dictionary, it will call loader() to
        populate its contents.  loader() must return something dict-like. Any
        elements set before the first read will be preserved.
        '''
        self._contents = {}
        self._loaded = False
        self._loader = loader
        self._deleted = set()

    def __getitem__(self, name):
        if not (self._loaded or name in self._contents or name in self._deleted):
            self.load()

        return self._contents[name]

    def __setitem__(self, name, value):
        self._contents[name] = value
        self._deleted.discard(name)

    def __delitem__(self, name):
        del self._contents[name]
        self._deleted.add(name)

    def __contains__(self, name):
        self.load()
        return name in self._contents

    def __len__(self):
        self.load()
        return len(self._contents)

    def __iter__(self):
        self.load()
        return iter(self._contents)

    def __repr__(self):
        self.load()
        return repr(self._contents)

    def load(self):
        if self._loaded:
            return

        loaded_contents = self._loader()
        loaded_contents.update(self._contents)
        self._contents = loaded_contents
        self._loaded = True

