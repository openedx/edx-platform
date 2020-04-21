"""
Experimentation serializers
"""


from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ExperimentData, ExperimentKeyValue

User = get_user_model()  # pylint:disable=invalid-name


class ExperimentDataCreateSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', default=serializers.CurrentUserDefault(), required=False,
                                        queryset=User.objects.all())

    class Meta(object):
        model = ExperimentData
        fields = ('id', 'experiment_id', 'user', 'key', 'value', 'created', 'modified',)


class ExperimentDataSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field='username', default=serializers.CurrentUserDefault())

    class Meta(ExperimentDataCreateSerializer.Meta):
        read_only_fields = ('user',)


class ExperimentKeyValueSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = ExperimentKeyValue
        fields = ('id', 'experiment_id', 'key', 'value', 'created', 'modified',)
