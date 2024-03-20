"""
API Serializers for textbooks page
"""

from rest_framework import serializers


class CourseTextbookChapterSerializer(serializers.Serializer):
    """
    Serializer for representing textbook chapter.
    """

    title = serializers.CharField()
    url = serializers.CharField()


class CourseTextbookItemSerializer(serializers.Serializer):
    """
    Serializer for representing textbook item.
    """

    id = serializers.CharField()
    chapters = CourseTextbookChapterSerializer(many=True)
    tab_title = serializers.CharField()


class CourseTextbooksSerializer(serializers.Serializer):
    """
    Serializer for representing course's textbooks.
    """

    textbooks = CourseTextbookItemSerializer(many=True)
