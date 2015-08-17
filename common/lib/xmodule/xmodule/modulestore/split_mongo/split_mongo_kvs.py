import copy
from contracts import contract, new_contract
from xblock.fields import Scope
from collections import namedtuple
from xblock.exceptions import InvalidScopeError
from .definition_lazy_loader import DefinitionLazyLoader
from xmodule.modulestore.inheritance import InheritanceKeyValueStore
from opaque_keys.edx.locator import BlockUsageLocator

# id is a BlockUsageLocator, def_id is the definition's guid
SplitMongoKVSid = namedtuple('SplitMongoKVSid', 'id, def_id')
new_contract('BlockUsageLocator', BlockUsageLocator)


class SplitMongoKVS(InheritanceKeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """

    VALID_SCOPES = (Scope.parent, Scope.children, Scope.settings, Scope.content)

    @contract(parent="BlockUsageLocator | None")
    def __init__(self, definition, initial_values, default_values, parent, field_decorator=None):
        """

        :param definition: either a lazyloader or definition id for the definition
        :param initial_values: a dictionary of the locally set values
        :param default_values: any Scope.settings field defaults that are set locally
            (copied from a template block with copy_from_template)
        """
        # deepcopy so that manipulations of fields does not pollute the source
        super(SplitMongoKVS, self).__init__(copy.deepcopy(initial_values))
        self._definition = definition  # either a DefinitionLazyLoader or the db id of the definition.
        # if the db id, then the definition is presumed to be loaded into _fields

        self._defaults = default_values
        # a decorator function for field values (to be called when a field is accessed)
        if field_decorator is None:
            self.field_decorator = lambda x: x
        else:
            self.field_decorator = field_decorator

        self.parent = parent

    def get(self, key):
        # load the field, if needed
        if key.field_name not in self._fields:
            # parent undefined in editing runtime (I think)
            if key.scope == Scope.parent:
                return self.parent
            if key.scope == Scope.children:
                # didn't find children in _fields; so, see if there's a default
                raise KeyError()
            elif key.scope == Scope.settings:
                # get default which may be the inherited value
                raise KeyError()
            elif key.scope == Scope.content:
                if isinstance(self._definition, DefinitionLazyLoader):
                    self._load_definition()
                else:
                    raise KeyError()
            else:
                raise InvalidScopeError(key, self.VALID_SCOPES)

        if key.field_name in self._fields:
            field_value = self._fields[key.field_name]

            # return the "decorated" field value
            return self.field_decorator(field_value)

        return None

    def set(self, key, value):
        # handle any special cases
        if key.scope not in self.VALID_SCOPES:
            raise InvalidScopeError(key, self.VALID_SCOPES)
        if key.scope == Scope.content:
            self._load_definition()

        # set the field
        self._fields[key.field_name] = value

        # This function is currently incomplete: it doesn't handle side effects.
        # To complete this function, here is some pseudocode for what should happen:
        #
        # if key.scope == Scope.children:
        #     remove inheritance from any exchildren
        #     add inheritance to any new children
        # if key.scope == Scope.settings:
        #     if inheritable, push down to children

    def delete(self, key):
        # handle any special cases
        if key.scope not in self.VALID_SCOPES:
            raise InvalidScopeError(key, self.VALID_SCOPES)
        if key.scope == Scope.content:
            self._load_definition()

        # delete the field value
        if key.field_name in self._fields:
            del self._fields[key.field_name]

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

    def default(self, key):
        """
        Check to see if the default should be from the template's defaults (if any)
        rather than the global default or inheritance.
        """
        if self._defaults and key.field_name in self._defaults:
            return self._defaults[key.field_name]
        # If not, try inheriting from a parent, then use the XBlock type's normal default value:
        return super(SplitMongoKVS, self).default(key)

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
