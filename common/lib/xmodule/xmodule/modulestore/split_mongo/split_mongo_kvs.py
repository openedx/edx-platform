import copy
from xblock.core import Scope
from collections import namedtuple
from xblock.runtime import KeyValueStore, InvalidScopeError
from .definition_lazy_loader import DefinitionLazyLoader

# id is a BlockUsageLocator, def_id is the definition's guid
SplitMongoKVSid = namedtuple('SplitMongoKVSid', 'id, def_id')


# TODO should this be here or w/ x_module or ???
class SplitMongoKVS(KeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """
    def __init__(self, definition, children, metadata, _inherited_metadata, location, category):
        """

        :param definition:
        :param children:
        :param metadata: the locally defined value for each metadata field
        :param _inherited_metadata: the value of each inheritable field from above this.
            Note, metadata may override and disagree w/ this b/c this says what the value
            should be if metadata is undefined for this field.
        """
        # ensure kvs's don't share objects w/ others so that changes can't appear in separate ones
        # the particular use case was that changes to kvs's were polluting caches. My thinking was
        # that kvs's should be independent thus responsible for the isolation.
        if isinstance(definition, DefinitionLazyLoader):
            self._definition = definition
        else:
            self._definition = copy.copy(definition)
        self._children = copy.copy(children)
        self._metadata = copy.copy(metadata)
        self._inherited_metadata = _inherited_metadata
        self._location = location
        self._category = category

    def get(self, key):
        if key.scope == Scope.children:
            return self._children
        elif key.scope == Scope.parent:
            return None
        elif key.scope == Scope.settings:
            if key.field_name in self._metadata:
                return self._metadata[key.field_name]
            elif key.field_name in self._inherited_metadata:
                return self._inherited_metadata[key.field_name]
            else:
                raise KeyError()
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                return self._location
            elif key.field_name == 'category':
                return self._category
            else:
                if isinstance(self._definition, DefinitionLazyLoader):
                    self._definition = self._definition.fetch()
                if (key.field_name == 'data' and
                    not isinstance(self._definition.get('data'), dict)):
                    return self._definition.get('data')
                elif 'data' not in self._definition or key.field_name not in self._definition['data']:
                    raise KeyError()
                else:
                    return self._definition['data'][key.field_name]
        else:
            raise InvalidScopeError(key.scope)

    def set(self, key, value):
        # TODO cache db update implications & add method to invoke
        if key.scope == Scope.children:
            self._children = value
            # TODO remove inheritance from any orphaned exchildren
            # TODO add inheritance to any new children
        elif key.scope == Scope.settings:
            # TODO if inheritable, push down to children who don't override
            self._metadata[key.field_name] = value
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                self._location = value
            elif key.field_name == 'category':
                self._category = value
            else:
                if isinstance(self._definition, DefinitionLazyLoader):
                    self._definition = self._definition.fetch()
                if (key.field_name == 'data' and
                    not isinstance(self._definition.get('data'), dict)):
                    self._definition.get('data')
                else:
                    self._definition.setdefault('data', {})[key.field_name] = value
        else:
            raise InvalidScopeError(key.scope)

    def delete(self, key):
        # TODO cache db update implications & add method to invoke
        if key.scope == Scope.children:
            self._children = []
        elif key.scope == Scope.settings:
            # TODO if inheritable, ensure _inherited_metadata has value from above and
            # revert children to that value
            if key.field_name in self._metadata:
                del self._metadata[key.field_name]
        elif key.scope == Scope.content:
            # don't allow deletion of location nor category
            if key.field_name == 'location':
                pass
            elif key.field_name == 'category':
                pass
            else:
                if isinstance(self._definition, DefinitionLazyLoader):
                    self._definition = self._definition.fetch()
                if (key.field_name == 'data' and
                    not isinstance(self._definition.get('data'), dict)):
                    self._definition.setdefault('data', None)
                else:
                    try:
                        del self._definition['data'][key.field_name]
                    except KeyError:
                        pass
        else:
            raise InvalidScopeError(key.scope)

    def has(self, key):
        if key.scope in (Scope.children, Scope.parent):
            return True
        elif key.scope == Scope.settings:
            return key.field_name in self._metadata or key.field_name in self._inherited_metadata
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                return True
            elif key.field_name == 'category':
                return self._category is not None
            else:
                if isinstance(self._definition, DefinitionLazyLoader):
                    self._definition = self._definition.fetch()
                if (key.field_name == 'data' and
                    not isinstance(self._definition.get('data'), dict)):
                    return self._definition.get('data') is not None
                else:
                    return key.field_name in self._definition.get('data', {})
        else:
            return False

    def get_data(self):
        """
        Intended only for use by persistence layer to get the native definition['data'] rep
        """
        if isinstance(self._definition, DefinitionLazyLoader):
            self._definition = self._definition.fetch()
        return self._definition.get('data')

    def get_own_metadata(self):
        """
        Get the metadata explicitly set on this element.
        """
        return self._metadata

    def get_inherited_metadata(self):
        """
        Get the metadata set by the ancestors (which own metadata may override or not)
        """
        return self._inherited_metadata

