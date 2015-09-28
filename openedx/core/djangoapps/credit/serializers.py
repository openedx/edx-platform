""" Credit API Serializers """

from rest_framework import serializers

from openedx.core.djangoapps.credit.models import CreditCourse


class CreditCourseSerializer(serializers.ModelSerializer):
    """ CreditCourse Serializer """

    class Meta(object):  # pylint: disable=missing-docstring
        model = CreditCourse
        exclude = ('id',)
