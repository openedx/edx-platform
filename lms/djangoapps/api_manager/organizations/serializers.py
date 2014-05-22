""" Django REST Framework Serializers """

from rest_framework import serializers

from api_manager.models import Organization


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for Organization model interactions """

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'workgroups', 'users', 'created', 'modified')
        read_only = ('url', 'id', 'created')
