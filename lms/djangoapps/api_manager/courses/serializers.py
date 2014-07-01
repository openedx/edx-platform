""" Django REST Framework Serializers """

from api_manager.models import CourseModuleCompletion
from api_manager.utils import generate_base_uri
from rest_framework import serializers


class CourseModuleCompletionSerializer(serializers.ModelSerializer):
    """ Serializer for CourseModuleCompletion model interactions """
    user_id = serializers.Field(source='user.id')

    class Meta:
        """ Serializer/field specification """
        model = CourseModuleCompletion
        fields = ('id', 'user_id', 'course_id', 'content_id', 'stage', 'created', 'modified')
        read_only = ('id', 'created')


class GradeSerializer(serializers.Serializer):
    """ Serializer for model interactions """
    grade = serializers.Field()


class CourseLeadersSerializer(serializers.Serializer):
    """ Serializer for course leaderboard """
    id = serializers.IntegerField(source='student__id')
    username = serializers.CharField(source='student__username')
    title = serializers.CharField(source='student__profile__title')
    avatar_url = serializers.CharField(source='student__profile__avatar_url')
    points_scored = serializers.SerializerMethodField('get_points_scored')

    def get_points_scored(self, obj):
        """
        formats points_scored to two decimal points
        """
        points_scored = obj['points_scored'] or 0
        return round(points_scored, 2)


class CourseCompletionsLeadersSerializer(serializers.Serializer):
    """ Serializer for course completions leaderboard """
    id = serializers.IntegerField(source='user__id')
    username = serializers.CharField(source='user__username')
    title = serializers.CharField(source='user__profile__title')
    avatar_url = serializers.CharField(source='user__profile__avatar_url')
    completions = serializers.IntegerField()


class CourseSerializer(serializers.Serializer):
    """ Serializer for Courses """
    id = serializers.CharField(source='id')
    name = serializers.CharField(source='display_name')
    category = serializers.CharField(source='location.category')
    number = serializers.CharField(source='location.course')
    org = serializers.CharField(source='location.org')
    uri = serializers.SerializerMethodField('get_uri')
    due = serializers.DateTimeField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    def get_uri(self, course):
        """
        Builds course detail uri
        """
        return "{}/{}".format(generate_base_uri(self.context['request']), course.id)

    class Meta:
        """ Serializer/field specification """
        #lookup_field = 'id'
        #fields = ('id', 'name', 'category', 'number', 'org', 'uri', 'due', 'start', 'end')
