"""
This module provides an abstraction for working objects that conceptually have
the following attributes:

    location: An identifier for an item, of which there might be many revisions
    children: A list of urls for other items required to fully define this object
    data: A set of nested data needed to define this object
    editor: The editor/owner of the object
    parents: Url pointers for objects that this object was derived from
    revision: What revision of the item this is
"""


class Location(object):
    ''' Encodes a location.
        Can be:
        * String (url)
        * Tuple
        * Dictionary
    '''
    def __init__(self, location):
        self.update(location)

    def update(self, location):
        if isinstance(location, basestring):
            self.tag = location.split('/')[0][:-1]
            (self.org, self.course, self.category, self.name) = location.split('/')[2:]
        elif isinstance(location, list):
            (self.tag, self.org, self.course, self.category, self.name) = location
        elif isinstance(location, dict):
            self.tag = location['tag']
            self.org = location['org']
            self.course = location['course']
            self.category = location['category']
            self.name = location['name']
        elif isinstance(location, Location):
            self.update(location.list())

    def url(self):
        return "i4x://{org}/{course}/{category}/{name}".format(**self.dict())

    def list(self):
        return [self.tag, self.org, self.course, self.category, self.name]

    def dict(self):
        return {'tag': self.tag,
                'org': self.org,
                'course': self.course,
                'category': self.category,
                'name': self.name}

    def to_json(self):
        return self.dict()


class KeyStore(object):
    def get_children_for_item(self, location):
        """
        Returns the children for the most recent revision of the object
        with the specified location.

        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError
        """
        raise NotImplementedError


class KeyStoreItem(object):
    """
    An object from a KeyStore, which can be saved back to that keystore
    """
    def __init__(self, location, children, data, editor, parents, revision):
        self.location = location
        self.children = children
        self.data = data
        self.editor = editor
        self.parents = parents
        self.revision = revision

    def save(self):
        raise NotImplementedError
