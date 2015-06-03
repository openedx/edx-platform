"""Fields useful for edX API implementations."""

from rest_framework.serializers import Field


class ExpandableField(Field):
    """Field that can dynamically use a more detailed serializer based on a user-provided "expand" parameter."""
    def __init__(self, **kwargs):
        """Sets up the ExpandableField with the collapsed and expanded versions of the serializer."""
        assert 'collapsed_serializer' in kwargs and 'expanded_serializer' in kwargs
        self.collapsed = kwargs.pop('collapsed_serializer')
        self.expanded = kwargs.pop('expanded_serializer')
        super(ExpandableField, self).__init__(**kwargs)

    def field_to_native(self, obj, field_name):
        """Converts obj to a native representation, using the expanded serializer if the context requires it."""
        if 'expand' in self.context and field_name in self.context['expand']:
            self.expanded.initialize(self, field_name)
            return self.expanded.field_to_native(obj, field_name)
        else:
            self.collapsed.initialize(self, field_name)
            return self.collapsed.field_to_native(obj, field_name)
