"""
Support for inheritance of fields down an XBlock hierarchy.
"""
from __future__ import absolute_import

from django.conf import settings
from openedx.core.lib.xblock_fields.inherited_fields import InheritanceMixin
from xblock.fields import Scope
from xblock.runtime import KeyValueStore, KvsFieldData


def compute_inherited_metadata(descriptor):
    """Given a descriptor, traverse all of its descendants and do metadata
    inheritance.  Should be called on a CourseDescriptor after importing a
    course.

    NOTE: This means that there is no such thing as lazy loading at the
    moment--this accesses all the children."""
    if descriptor.has_children:
        parent_metadata = descriptor.xblock_kvs.inherited_settings.copy()
        # add any of descriptor's explicitly set fields to the inheriting list
        for field in InheritanceMixin.fields.values():
            if field.is_set_on(descriptor):
                # inherited_settings values are json repr
                parent_metadata[field.name] = field.read_json(descriptor)

        for child in descriptor.get_children():
            inherit_metadata(child, parent_metadata)
            compute_inherited_metadata(child)


def inherit_metadata(descriptor, inherited_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited

    `inherited_data`: A dictionary mapping field names to the values that
        they should inherit
    """
    try:
        descriptor.xblock_kvs.inherited_settings = inherited_data
    except AttributeError:  # the kvs doesn't have inherited_settings probably b/c it's an error module
        pass


def own_metadata(module):
    """
    Return a JSON-friendly dictionary that contains only non-inherited field
    keys, mapped to their serialized values
    """
    return module.get_explicitly_set_fields_by_scope(Scope.settings)


class InheritingFieldData(KvsFieldData):
    """A `FieldData` implementation that can inherit value from parents to children."""

    def __init__(self, inheritable_names, **kwargs):
        """
        `inheritable_names` is a list of names that can be inherited from
        parents.

        """
        super(InheritingFieldData, self).__init__(**kwargs)
        self.inheritable_names = set(inheritable_names)

    def has_default_value(self, name):
        """
        Return whether or not the field `name` has a default value
        """
        has_default_value = getattr(self._kvs, 'has_default_value', False)
        if callable(has_default_value):
            return has_default_value(name)

        return has_default_value

    def default(self, block, name):
        """
        The default for an inheritable name is found on a parent.
        """
        if name in self.inheritable_names:
            # Walk up the content tree to find the first ancestor
            # that this field is set on. Use the field from the current
            # block so that if it has a different default than the root
            # node of the tree, the block's default will be used.
            field = block.fields[name]
            ancestor = block.get_parent()
            # In case, if block's parent is of type 'library_content',
            # bypass inheritance and use kvs' default instead of reusing
            # from parent as '_copy_from_templates' puts fields into
            # defaults.
            if ancestor and \
               ancestor.location.category == 'library_content' and \
               self.has_default_value(name):
                return super(InheritingFieldData, self).default(block, name)

            while ancestor is not None:
                if field.is_set_on(ancestor):
                    return field.read_json(ancestor)
                else:
                    ancestor = ancestor.get_parent()
        return super(InheritingFieldData, self).default(block, name)


def inheriting_field_data(kvs):
    """Create an InheritanceFieldData that inherits the names in InheritanceMixin."""
    return InheritingFieldData(
        inheritable_names=InheritanceMixin.fields.keys(),
        kvs=kvs,
    )


class InheritanceKeyValueStore(KeyValueStore):
    """
    Common superclass for kvs's which know about inheritance of settings. Offers simple
    dict-based storage of fields and lookup of inherited values.

    Note: inherited_settings is a dict of key to json values (internal xblock field repr)
    """
    def __init__(self, initial_values=None, inherited_settings=None):
        super(InheritanceKeyValueStore, self).__init__()
        self.inherited_settings = inherited_settings or {}
        self._fields = initial_values or {}

    def get(self, key):
        return self._fields[key.field_name]

    def set(self, key, value):
        # xml backed courses are read-only, but they do have some computed fields
        self._fields[key.field_name] = value

    def delete(self, key):
        del self._fields[key.field_name]

    def has(self, key):
        return key.field_name in self._fields

    def default(self, key):
        """
        Check to see if the default should be from inheritance. If not
        inheriting, this will raise KeyError which will cause the caller to use
        the field's global default.
        """
        return self.inherited_settings[key.field_name]
