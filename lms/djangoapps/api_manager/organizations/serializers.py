""" Django REST Framework Serializers """

from rest_framework import serializers

from api_manager.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """ Serializer for Organization model interactions """
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'display_name', 'contact_name', 'contact_email', 'contact_phone', 'workgroups',
                  'users', 'groups', 'created', 'modified')
        read_only = ('url', 'id', 'created')
