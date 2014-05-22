""" Django REST Framework Serializers """

from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from .models import Workgroup, Project, Submission
from .models import SubmissionReview, PeerReview


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = User
        fields = ('id', 'url', 'username', 'email')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    name = serializers.SerializerMethodField('get_group_name')

    def get_group_name(self, group):
        """
        Group name is actually stored on the profile record, in order to
        allow for duplicate name values in the system.
        """
        try:
            group_profile = group.groupprofile
            if group_profile:
                return group_profile.name
        except ObjectDoesNotExist:
            return group.name

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Group
        fields = ('id', 'url', 'name')


class WorkgroupSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    groups = GroupSerializer(many=True, required=False)
    users = UserSerializer(many=True, required=False)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Workgroup
        fields = ('id', 'url', 'created', 'modified', 'name', 'groups', 'users')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    workgroups = WorkgroupSerializer(many=True, required=False)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Project
        fields = ('id', 'url', 'created', 'modified', 'course_id', 'content_id', 'workgroups')


class SubmissionSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    user = serializers.PrimaryKeyRelatedField(required=True)
    project = serializers.PrimaryKeyRelatedField(required=True)
    workgroup = serializers.PrimaryKeyRelatedField(required=True)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Submission
        fields = ('id', 'url', 'created', 'modified', 'user', 'project', 'workgroup', 'document_id', 'document_url', 'document_mime_type')


class SubmissionReviewSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    submission = serializers.PrimaryKeyRelatedField(required=True)
    reviewer = serializers.PrimaryKeyRelatedField(required=True)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = SubmissionReview
        fields = ('id', 'url', 'created', 'modified', 'submission', 'reviewer', 'question', 'answer')


class PeerReviewSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    user = serializers.PrimaryKeyRelatedField(required=True)
    reviewer = serializers.PrimaryKeyRelatedField(required=True)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = PeerReview
        fields = ('id', 'url', 'created', 'modified', 'user', 'reviewer', 'question', 'answer')
