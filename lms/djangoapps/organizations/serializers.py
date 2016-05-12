""" Django REST Framework Serializers """
from rest_framework import serializers

from organizations.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """ Serializer for Organization model interactions """
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'display_name', 'contact_name', 'contact_email', 'contact_phone',
                  'logo_url', 'workgroups', 'users', 'groups', 'created', 'modified')
        read_only = ('url', 'id', 'created')


class BasicOrganizationSerializer(serializers.ModelSerializer):
    """ Serializer for Basic Organization fields """
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'display_name', 'contact_name', 'contact_email', 'contact_phone',
                  'logo_url', 'created', 'modified')
        read_only = ('url', 'id', 'created',)


class OrganizationWithCourseCountSerializer(BasicOrganizationSerializer):
    """ Serializer for Organization fields with number of courses """
    number_of_courses = serializers.IntegerField(source='number_of_courses')

    class Meta(object):
        """ Serializer/field specification """
        model = Organization
        fields = ('url', 'id', 'name', 'display_name', 'number_of_courses', 'contact_name', 'contact_email',
                  'contact_phone', 'logo_url', 'created', 'modified')
