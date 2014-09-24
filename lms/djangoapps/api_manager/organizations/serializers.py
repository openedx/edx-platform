""" Django REST Framework Serializers """
from django.contrib.auth.models import User

from rest_framework import serializers

from api_manager.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """ Serializer for Organization model interactions """
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'display_name', 'contact_name', 'contact_email', 'contact_phone'
                  , 'logo_url', 'workgroups', 'users', 'groups', 'created', 'modified')
        read_only = ('url', 'id', 'created')


class BasicOrganizationSerializer(serializers.ModelSerializer):
    """ Serializer for Basic Organization fields """
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'created', 'display_name', 'logo_url')
        read_only = ('url', 'id', 'created',)
