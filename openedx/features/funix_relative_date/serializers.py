from rest_framework import serializers

from lms.djangoapps.course_home_api.dates.serializers import DatesTabSerializer


class FUNiXDatesTabSerializer(DatesTabSerializer):
	"""
	Serializer for the FUNiX Dates Tab
	"""
	goal_hours_per_day = serializers.FloatField()
	goal_weekdays = serializers.ListField(child=serializers.BooleanField())
