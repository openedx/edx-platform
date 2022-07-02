""" Serializer for UserTourView. """

from rest_framework import serializers

from lms.djangoapps.user_tours.models import UserTour


class UserTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTour
        fields = ['course_home_tour_status', 'show_courseware_tour']
