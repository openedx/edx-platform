""" Django REST Framework Serializers """

import json

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers


class GroupSerializer(serializers.Serializer):
    """ Serializer for model interactions """
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField('get_group_name')
    type = serializers.SerializerMethodField('get_group_type')
    data = serializers.SerializerMethodField('get_group_data')
    url = serializers.SerializerMethodField('get_group_url')

    def get_group_name(self, group):
        """
        Group name is actually stored on the profile record, in order to
        allow for duplicate name values in the system.
        """
        try:
            group_profile = group.groupprofile
            if group_profile and group_profile.name:
                return group_profile.name
            else:
                return group.name
        except ObjectDoesNotExist:
            return group.name

    def get_group_type(self, group):
        """
        Loads data from group profile
        """
        try:
            group_profile = group.groupprofile
            return group_profile.group_type
        except ObjectDoesNotExist:
            return None

    def get_group_data(self, group):
        """
        Loads data from group profile
        """
        try:
            group_profile = group.groupprofile
            if group_profile.data:
                return json.loads(group_profile.data)
        except ObjectDoesNotExist:
            return None

    def get_group_url(self, group):
        """
        Builds a URL for resource referencing
        """
        return '/api/server/groups/{}'.format(group.id)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Group
        lookup_field = 'id'
        fields = ('id', 'name', 'type', 'data', 'url')
