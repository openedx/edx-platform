import copy
from xblock.core import Scope
from collections import namedtuple
from xblock.runtime import KeyValueStore, InvalidScopeError
from .definition_lazy_loader import DefinitionLazyLoader

# id is a BlockUsageLocator, def_id is the definition's guid
SplitMongoKVSid = namedtuple('SplitMongoKVSid', 'id, def_id')


PROVENANCE_LOCAL = 'local'
PROVENANCE_DEFAULT = 'default'
PROVENANCE_INHERITED = 'inherited'

class SplitMongoKVS(KeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """

    def __init__(self, definition, fields, _inherited_settings, location, category):
        """

        :param definition: either a lazyloader or definition id for the definition
        :param fields: a dictionary of the locally set fields
        :param _inherited_settings: the value of each inheritable field from above this.
            Note, local fields may override and disagree w/ this b/c this says what the value
            should be if the field is undefined.
        """
        # ensure kvs's don't share objects w/ others so that changes can't appear in separate ones
        # the particular use case was that changes to kvs's were polluting caches. My thinking was
        # that kvs's should be independent thus responsible for the isolation.
        self._definition = definition  # either a DefinitionLazyLoader or the db id of the definition.
        # if the db id, then the definition is presumed to be loaded into _fields
        self._fields = copy.copy(fields)
        self._inherited_settings = _inherited_settings
        self._location = location
        self._category = category

    def get(self, key):
        # simplest case, field is directly set
        if key.field_name in self._fields:
            return self._fields[key.field_name]

        # parent undefined in editing runtime (I think)
        if key.scope == Scope.parent:
            # see STUD-624. Right now copies MongoKeyValueStore.get's behavior of returning None
            return None
        if key.scope == Scope.children:
            # didn't find children in _fields; so, see if there's a default
            raise KeyError()
        elif key.scope == Scope.settings:
            # didn't find in _fields; so, get from inheritance since not locally set
            if key.field_name in self._inherited_settings:
                return self._inherited_settings[key.field_name]
            else:
                # or get default
                raise KeyError()
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                return self._location
            elif key.field_name == 'category':
                return self._category
            elif isinstance(self._definition, DefinitionLazyLoader):
                self._load_definition()
                if key.field_name in self._fields:
                    return self._fields[key.field_name]

            raise KeyError()
        else:
            raise InvalidScopeError(key.scope)

    def set(self, key, value):
        # handle any special cases
        if key.scope not in [Scope.children, Scope.settings, Scope.content]:
            raise InvalidScopeError(key.scope)
        if key.scope == Scope.content:
            if key.field_name == 'location':
                self._location = value  # is changing this legal?
                return
            elif key.field_name == 'category':
                # TODO should this raise an exception? category is not changeable.
                return
            else:
                self._load_definition()

        # set the field
        self._fields[key.field_name] = value

        # handle any side effects -- story STUD-624
        # if key.scope == Scope.children:
            # STUD-624 remove inheritance from any exchildren
            # STUD-624 add inheritance to any new children
        # if key.scope == Scope.settings:
            # STUD-624 if inheritable, push down to children

    def delete(self, key):
        # handle any special cases
        if key.scope not in [Scope.children, Scope.settings, Scope.content]:
            raise InvalidScopeError(key.scope)
        if key.scope == Scope.content:
            if key.field_name == 'location':
                return  # noop
            elif key.field_name == 'category':
                # TODO should this raise an exception? category is not deleteable.
                return  # noop
            else:
                self._load_definition()

        # delete the field value
        if key.field_name in self._fields:
            del self._fields[key.field_name]

        # handle any side effects
        # if key.scope == Scope.children:
            # STUD-624 remove inheritance from any exchildren
        # if key.scope == Scope.settings:
            # STUD-624 if inheritable, push down _inherited_settings value to children

    def has(self, key):
        """
        Is the given field explicitly set in this kvs (not inherited nor default)
        """
        # handle any special cases
        if key.scope == Scope.content:
            if key.field_name == 'location':
                return True
            elif key.field_name == 'category':
                return self._category is not None
            else:
                self._load_definition()
        elif key.scope == Scope.parent:
            return True

        # it's not clear whether inherited values should return True. Right now they don't
        # if someone changes it so that they do, then change any tests of field.name in xx._model_data
        return key.field_name in self._fields

    # would like to just take a key, but there's a bunch of magic in DbModel for constructing the key via
    # a private method
    def field_value_provenance(self, key_scope, key_name):
        """
        Where the field value comes from: one of [PROVENANCE_LOCAL, PROVENANCE_DEFAULT, PROVENANCE_INHERITED].
        """
        # handle any special cases
        if key_scope == Scope.content:
            if key_name == 'location':
                return PROVENANCE_LOCAL
            elif key_name == 'category':
                return PROVENANCE_LOCAL
            else:
                self._load_definition()
                if key_name in self._fields:
                    return PROVENANCE_LOCAL
                else:
                    return PROVENANCE_DEFAULT
        elif key_scope == Scope.parent:
            return PROVENANCE_DEFAULT
        # catch the locally set state
        elif key_name in self._fields:
            return PROVENANCE_LOCAL
        elif key_scope == Scope.settings and key_name in self._inherited_settings:
            return PROVENANCE_INHERITED
        else:
            return PROVENANCE_DEFAULT

    def get_inherited_settings(self):
        """
        Get the settings set by the ancestors (which locally set fields may override or not)
        """
        return self._inherited_settings

    def _load_definition(self):
        """
        Update fields w/ the lazily loaded definitions
        """
        if isinstance(self._definition, DefinitionLazyLoader):
            persisted_definition = self._definition.fetch()
            if persisted_definition is not None:
                self._fields.update(persisted_definition.get('fields'))
                # do we want to cache any of the edit_info?
            self._definition = None  # already loaded
