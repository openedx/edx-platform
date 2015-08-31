"""Fields useful for edX API implementations."""
from rest_framework.serializers import Field


class ExpandableField(Field):
    """Field that can dynamically use a more detailed serializer based on a user-provided "expand" parameter.

    Kwargs:
      collapsed_serializer (Serializer): the serializer to use for a non-expanded representation.
      expanded_serializer (Serializer): the serializer to use for an expanded representation.
      exclude_expand_fields (set(str)): a set of fields which will not be expanded by sub-serializers.
    """
    def __init__(self, **kwargs):
        """Sets up the ExpandableField with the collapsed and expanded versions of the serializer."""
        assert 'collapsed_serializer' in kwargs and 'expanded_serializer' in kwargs
        self.collapsed = kwargs.pop('collapsed_serializer')
        self.expanded = kwargs.pop('expanded_serializer')
        self.exclude_expand_fields = kwargs.pop('exclude_expand_fields', set())
        super(ExpandableField, self).__init__(**kwargs)

    def to_representation(self, obj):
        """
        Return a representation of the field that is either expanded or collapsed.
        """
        should_expand = self.field_name in self.context.get("expand", [])
        field = self.expanded if should_expand else self.collapsed

        # Avoid double-binding the field, otherwise we'll get
        # an error about the source kwarg being redundant.
        if field.source is None:
            field.bind(self.field_name, self)

            # Exclude fields that should not be expanded in the nested field
            if should_expand:
                nested_expand_fields = set(field.context.get("expand", []))
                self.expanded.context["expand"] = list(nested_expand_fields - self.exclude_expand_fields)

        return field.to_representation(obj)
