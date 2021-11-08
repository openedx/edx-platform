"""
Serializers for course_rating
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from openedx.features.course_rating.models import CourseRating, CourseAverageRating
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for "CourseRating" model
    """
    course_rating = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    course_title = serializers.SerializerMethodField()
    moderated_by_username = serializers.SerializerMethodField()

    class Meta:
        model = CourseRating
        fields = [
            'id', 'course', 'course_title', 'username', 'course_rating', 'rating',
            'comment', 'is_approved', 'user', 'moderated_by', 'moderated_by_username',
        ]

    def get_course_rating(self, obj):
        course_avg_rating = CourseAverageRating.objects.filter(course=obj.course).first()
        return CourseAverageRatingSerializer(course_avg_rating).data

    def get_course_title(self, obj):
        """
        Get course title from "CourseOverview" model.
        """
        course_overview = CourseOverview.objects.filter(id=obj.course).first()
        return course_overview.display_name if course_overview else ''

    def get_moderated_by_username(self, obj):
        """
        Get moderator username title from "CourseRating" model.
        """
        return obj.moderated_by.username if obj.moderated_by else ''

    def update(self, instance, validated_data):
        """
        Override update method to map moderated_by using username.
        """
        request = self.context['request']
        moderated_by_username = request.data.get('moderated_by_username', None)

        if moderated_by_username:
            moderated_by = User.objects.filter(username=moderated_by_username).first()
            validated_data['moderated_by'] = moderated_by if moderated_by else ''

        return super().update(instance, validated_data)


class CourseAverageRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for "CourseAverageRating" model
    """
    class Meta:
        model = CourseAverageRating
        fields = ['average_rating', 'total_raters']


class CourseAverageRatingListSerializer(serializers.ModelSerializer):
    """
    Serializer for "CourseAverageRatingListSerializer" model
    """
    class Meta:
        model = CourseAverageRating
        fields = ['course', 'average_rating', 'total_raters']
