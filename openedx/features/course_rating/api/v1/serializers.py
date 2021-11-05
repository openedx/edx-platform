"""
Serializers for course_rating
"""
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

    class Meta:
        model = CourseRating
        fields = [
            'id', 'course', 'course_title', 'username', 'course_rating', 'rating',
            'comment', 'is_approved', 'user', 'moderated_by'
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
