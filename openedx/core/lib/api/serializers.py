"""
Serializers to be used in APIs.
"""

from rest_framework import serializers


class CollapsedReferenceSerializer(serializers.HyperlinkedModelSerializer):
    """Serializes arbitrary models in a collapsed format, with just an id and url."""
    url = serializers.HyperlinkedIdentityField(view_name='')

    def __init__(self, model_class, view_name, id_source='id', lookup_field=None, *args, **kwargs):
        """Configures the serializer.

        Args:
            model_class (class): Model class to serialize.
            view_name (string): Name of the Django view used to lookup the
                model.
            id_source (string): Optional name of the id field on the model.
                Defaults to 'id'. Also used as the property name of the field
                in the serialized representation.
            lookup_field (string): Optional name of the model field used to
                lookup the model in the view. Defaults to the value of
                id_source.
        """
        if not lookup_field:
            lookup_field = id_source

        self.Meta.model = model_class

        super(CollapsedReferenceSerializer, self).__init__(*args, **kwargs)

        self.fields[id_source] = serializers.CharField(read_only=True)
        self.fields['url'].view_name = view_name
        self.fields['url'].lookup_field = lookup_field
        self.fields['url'].lookup_url_kwarg = lookup_field

    class Meta(object):
        fields = ("url",)
