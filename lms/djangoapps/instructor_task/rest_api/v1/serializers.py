"""
Instructor Task Django app REST API serializers.
"""
import json

from django.apps import apps
from rest_framework import serializers

from lms.djangoapps.bulk_email.api import get_course_email
from lms.djangoapps.instructor_task.models import InstructorTaskSchedule


class SenderField(serializers.RelatedField):
    """
    Serializer field that converts the user object id to a human readable name (username)
    """
    def to_representation(self, value):
        return value.username


class TargetListField(serializers.RelatedField):
    """
    Serializer field that converts the email target values (recipient groups) of a message from an int to a human
    readable name.
    """
    def to_representation(self, value):
        return value.short_display()


class CourseEmailSerializer(serializers.ModelSerializer):
    """
    Serializer for the course email instance belonging to each scheduled task.
    """
    targets = TargetListField(many=True, read_only=True)
    sender = SenderField(many=False, read_only=True)

    class Meta:
        # use the bulk_email app's CourseEmail model without adding the direct import of the model
        course_email_model = apps.get_model('bulk_email.CourseEmail')
        model = course_email_model
        fields = (
            "id",
            "subject",
            "html_message",
            "text_message",
            "course_id",
            "to_option",
            "sender",
            "targets"
        )


class ScheduledBulkEmailSerializer(serializers.ModelSerializer):
    """
    Serializer for scheduled bulk email instructor tasks.
    """
    course_email = serializers.SerializerMethodField()

    class Meta:
        model = InstructorTaskSchedule
        fields = (
            "id",
            "course_email",
            "task",
            "task_due",
        )

    def get_course_email(self, obj):
        """
        This function is responsible for retrieving and including course email instance information associated with
        each individual scheduled task. Uses the task related to the schedule to extract the email id of the scheduled
        message. From here we can lookup the individual message and attach it with the other API results.
        """
        # extract the id of the course email instance for this task
        task_input = json.loads(obj.task.task_input)
        email_id = task_input["email_id"]
        # retrieve the course_email instance
        course_email = get_course_email(email_id)
        return CourseEmailSerializer(course_email).data
