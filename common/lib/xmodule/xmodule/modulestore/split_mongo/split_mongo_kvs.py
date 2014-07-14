import copy
from xblock.fields import Scope
from collections import namedtuple
from xblock.exceptions import InvalidScopeError
from .definition_lazy_loader import DefinitionLazyLoader
from xmodule.modulestore.inheritance import InheritanceKeyValueStore

# id is a BlockUsageLocator, def_id is the definition's guid
SplitMongoKVSid = namedtuple('SplitMongoKVSid', 'id, def_id')


class SplitMongoKVS(InheritanceKeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """

    def __init__(self, definition, fields, inherited_settings):
        """

        :param definition: either a lazyloader or definition id for the definition
        :param fields: a dictionary of the locally set fields
        :param inherited_settings: the json value of each inheritable field from above this.
            Note, local fields may override and disagree w/ this b/c this says what the value
            should be if the field is undefined.
        """
        # deepcopy so that manipulations of fields does not pollute the source
        super(SplitMongoKVS, self).__init__(copy.deepcopy(fields), inherited_settings)
        self._definition = definition  # either a DefinitionLazyLoader or the db id of the definition.
        # if the db id, then the definition is presumed to be loaded into _fields


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
            # get default which may be the inherited value
            raise KeyError()
        elif key.scope == Scope.content:
            if isinstance(self._definition, DefinitionLazyLoader):
                self._load_definition()
                if key.field_name in self._fields:
                    return self._fields[key.field_name]

            raise KeyError()
        else:
            raise InvalidScopeError(key)

    def set(self, key, value):
        # handle any special cases
        if key.scope not in [Scope.children, Scope.settings, Scope.content]:
            raise InvalidScopeError(key)
        if key.scope == Scope.content:
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
            raise InvalidScopeError(key)
        if key.scope == Scope.content:
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
            self._load_definition()
        elif key.scope == Scope.parent:
            return True

        # it's not clear whether inherited values should return True. Right now they don't
        # if someone changes it so that they do, then change any tests of field.name in xx._field_data
        return key.field_name in self._fields

    def _load_definition(self):
        """
        Update fields w/ the lazily loaded definitions
        """
        if isinstance(self._definition, DefinitionLazyLoader):
            persisted_definition = self._definition.fetch()
            if persisted_definition is not None:
                fields = self._definition.field_converter(persisted_definition.get('fields'))
                self._fields.update(fields)
                # do we want to cache any of the edit_info?
            self._definition = None  # already loaded
