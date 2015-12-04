""" Django REST Framework Serializers """

from django.contrib.auth.models import User

from rest_framework import serializers

from api_manager.groups.serializers import GroupSerializer
from .models import Project, Workgroup, WorkgroupSubmission
from .models import WorkgroupReview, WorkgroupSubmissionReview, WorkgroupPeerReview


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = User
        fields = ('id', 'url', 'username', 'email')


class ExtendedUserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """

    class Meta(object):
        """ Meta class for defining additional serializer characteristics """
        model = User
        fields = ('id', 'url', 'username', 'email', 'first_name', 'last_name')


class GradeSerializer(serializers.Serializer):
    """ Serializer for model interactions """
    grade = serializers.Field()


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    workgroups = serializers.PrimaryKeyRelatedField(many=True, required=False)
    organization = serializers.PrimaryKeyRelatedField(required=False)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Project
        fields = (
            'id', 'url', 'created', 'modified', 'course_id', 'content_id',
            'organization', 'workgroups'
        )


class WorkgroupSubmissionSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    user = serializers.PrimaryKeyRelatedField(required=True)
    workgroup = serializers.PrimaryKeyRelatedField(required=True)
    reviews = serializers.PrimaryKeyRelatedField(many=True, required=False)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = WorkgroupSubmission
        fields = (
            'id', 'url', 'created', 'modified', 'document_id', 'document_url',
            'document_mime_type', 'document_filename',
            'user', 'workgroup', 'reviews'
        )


class WorkgroupReviewSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    workgroup = serializers.PrimaryKeyRelatedField(required=True)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = WorkgroupReview
        fields = (
            'id', 'url', 'created', 'modified', 'question', 'answer',
            'workgroup', 'reviewer', 'content_id'
        )


class WorkgroupSubmissionReviewSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    submission = serializers.PrimaryKeyRelatedField(required=True, queryset=WorkgroupSubmission.objects.all())

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = WorkgroupSubmissionReview
        fields = (
            'id', 'url', 'created', 'modified', 'question', 'answer',
            'submission', 'reviewer', 'content_id'
        )


class WorkgroupPeerReviewSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    workgroup = serializers.PrimaryKeyRelatedField(required=True)
    user = serializers.PrimaryKeyRelatedField(required=True)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = WorkgroupPeerReview
        fields = (
            'id', 'url', 'created', 'modified', 'question', 'answer',
            'workgroup', 'user', 'reviewer', 'content_id'
        )


class WorkgroupSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for model interactions """
    project = serializers.PrimaryKeyRelatedField(required=True)
    groups = GroupSerializer(many=True, required=False)
    users = ExtendedUserSerializer(many=True, required=False)
    submissions = serializers.PrimaryKeyRelatedField(many=True, required=False)
    workgroup_reviews = serializers.PrimaryKeyRelatedField(many=True, required=False)
    peer_reviews = serializers.PrimaryKeyRelatedField(many=True, required=False)

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Workgroup
        fields = (
            'id', 'url', 'created', 'modified', 'name', 'project',
            'groups', 'users', 'submissions',
            'workgroup_reviews', 'peer_reviews'
        )


class BasicWorkgroupSerializer(serializers.HyperlinkedModelSerializer):
    """ Basic Workgroup Serializer to keep only basic fields """

    class Meta:
        """ Meta class for defining additional serializer characteristics """
        model = Workgroup
        fields = (
            'id', 'url', 'created', 'modified', 'name', 'project',
        )
