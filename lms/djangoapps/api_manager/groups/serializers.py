import json
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import Group
from rest_framework import serializers


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    name = serializers.SerializerMethodField('get_group_name')
    type = serializers.SerializerMethodField('get_group_type')
    data = serializers.SerializerMethodField('get_group_data')

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

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Group
        fields = ('id', 'url', 'name', 'type', 'data')

