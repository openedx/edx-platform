from rest_framework import pagination, serializers


class PaginationSerializer(pagination.PaginationSerializer):
    """
    Custom PaginationSerializer to include num_pages field
    """
    num_pages = serializers.Field(source='paginator.num_pages')


class CollapsedReferenceSerializer(serializers.HyperlinkedModelSerializer):
    """Serializes arbitrary models in a collapsed format, with just an id and url."""
    id = serializers.CharField(read_only=True)  # pylint: disable=invalid-name
    url = serializers.HyperlinkedIdentityField(view_name='')

    def __init__(self, model_class, view_name, id_source='id', lookup_field=None, *args, **kwargs):
        """Configures the serializer.

        Args:
            model_class (class): Model class to serialize.
            view_name (string): Name of the Django view used to lookup the
                model.
            id_source (string): Optional name of the id field on the model.
                Defaults to 'id'.
            lookup_field (string): Optional name of the model field used to
                lookup the model in the view. Defaults to the value of
                id_source.
        """
        if not lookup_field:
            lookup_field = id_source

        self.Meta.model = model_class

        super(CollapsedReferenceSerializer, self).__init__(*args, **kwargs)

        self.fields['id'].source = id_source
        self.fields['url'].view_name = view_name
        self.fields['url'].lookup_field = lookup_field

    class Meta(object):
        """Defines meta information for the ModelSerializer.

        model is set dynamically in __init__.
        """
        fields = ("id", "url")
