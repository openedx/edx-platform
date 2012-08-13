from utils import *

class Model(object):

    accessible_fields = ['id']
    base_url = None
    default_retrieve_params = {}

    DEFAULT_ACTIONS_WITH_ID = ['get', 'put', 'delete']
    DEFAULT_ACTIONS_WITHOUT_ID = ['get_all', 'post']
    DEFAULT_ACTIONS = DEFAULT_ACTIONS_WITH_ID + DEFAULT_ACTIONS_WITHOUT_ID

    def __init__(self, *args, **kwargs):
        self.attributes = extract(kwargs, self.accessible_fields)
        self.retrieved = False

    def __getattr__(self, name):
        if name == 'id':
            return self.attributes.get('id', None)
        try:
            return self.attributes[name]
        except KeyError:
            if self.retrieved or self.id == None:
                raise AttributeError("Field {0} does not exist".format(name))
            self.retrieve()
            return self.__getattr__(name)
    
    def __setattr__(self, name, value):
        if name == 'attributes' or name not in self.accessible_fields:
            super(Model, self).__setattr__(name, value)
        else:
            self.attributes[name] = value

    def __getitem__(self, key):
        if key not in self.accessible_fields:
            raise KeyError("Field {0} does not exist".format(key))
        return self.attributes.get(key)

    def __setitem__(self, key, value):
        if key not in self.accessible_fields:
            raise KeyError("Field {0} does not exist".format(key))
        self.attributes.__setitem__(key, value)

    def get(self, *args, **kwargs):
        return self.attributes.get(*args, **kwargs)

    def to_dict(self):
        self.retrieve()
        return self.attributes

    def retrieve(self, *args, **kwargs):
        if not self.retrieved:
            self._retrieve(*args, **kwargs)
            self.retrieved = True
        return self

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', id=self.id)
        response = perform_request('get', url, self.default_retrieve_params)
        self.update_attributes(**response)

    @classmethod
    def find(cls, id):
        return cls(id=id)

    def update_attributes(self, *args, **kwargs):
        for k, v in kwargs.items():
            if k in self.accessible_fields:
                self.__setattr__(k, v)
            else:
                raise AttributeError("Field {0} does not exist".format(k))
        
    def save(self):
        if self.id: # if we have id already, treat this as an update
            url = self.url(action='put', id=self.id)
            response = perform_request('put', url, self.attributes)
        else: # otherwise, treat this as an insert
            url = self.url(action='post', id=self.id)
            response = perform_request('post', url, self.attributes)
        self.retrieved = True
        self.update_attributes(**response)

    @classmethod
    def url_with_id(cls, *args, **kwargs):
        return cls.base_url + '/' + str(kwargs.get('id'))

    @classmethod
    def url_without_id(cls, *args, **kwargs):
        return cls.base_url

    @classmethod
    def url(cls, *args, **kwargs):
        if cls.base_url is None:
            raise CommentClientError("Must provide base_url when using default url function")
        id = kwargs.get('id')
        action = kwargs.get('action')
        if not action:
            raise CommentClientError("Must provide action")
        elif action not in cls.DEFAULT_ACTIONS:
            raise ValueError("Invalid action {0}. The supported action must be in {1}".format(action, str(cls.DEFAULT_ACTIONS)))
        elif action in cls.DEFAULT_ACTIONS_WITH_ID:
            if not id:
                raise CommentClientError("Cannot perform action {0} without id".format(action))
            return cls.url_with_id(id=id)
        else: # action must be in DEFAULT_ACTIONS_WITHOUT_ID now
            return cls.url_without_id()
