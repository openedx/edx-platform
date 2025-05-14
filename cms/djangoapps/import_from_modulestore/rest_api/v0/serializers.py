from rest_framework.serializers import ModelSerializer
from user_tasks.serializers import StatusSerializer

from ...models import Import


class ImportSerializer(ModelSerializer):
    class Meta:
        model = Import


class StatusWithImportSerializer(StatusSerializer):
    import_event = ImportSerializer()

    class Meta:
        model = StatusSerializer.Meta.model
        fields = [*StatusSerializer.Meta.fields, 'import_event']

