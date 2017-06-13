from rest_framework import serializers

from .models import ExperimentData


class ExperimentDataSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field='username', default=serializers.CurrentUserDefault())

    class Meta(object):
        model = ExperimentData
        fields = ('id', 'experiment_id', 'user', 'key', 'value', 'created', 'modified',)
        read_only_fields = ('user',)
