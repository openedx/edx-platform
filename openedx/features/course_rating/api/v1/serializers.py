"""
Serializers for course_rating
"""
from rest_framework import serializers

from openedx.features.course_rating.models import CourseRating, CourseAverageRating


class CourseRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for "CourseRating" model
    """
    course_rating = serializers.SerializerMethodField()

    class Meta:
        model = CourseRating
        fields = ['id', 'course', 'course_rating', 'rating', 'comment', 'is_approved', 'user', 'moderated_by']

    def get_course_rating(self, obj):
        course_avg_rating = CourseAverageRating.objects.filter(course=obj.course).first()
        return CourseAverageRatingSerializer(course_avg_rating).data


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
