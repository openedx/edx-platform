# pylint: disable=invalid-name
"""Signals related to the comments service."""

from django.dispatch import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from openedx.core.djangoapps.course_groups.models import CourseCohortsSettings

from .utils import set_course_discussion_settings
from .models import CourseDiscussionSettings

thread_created = Signal(providing_args=['user', 'post'])
thread_edited = Signal(providing_args=['user', 'post'])
thread_voted = Signal(providing_args=['user', 'post'])
thread_deleted = Signal(providing_args=['user', 'post', 'involved_users'])
thread_followed = Signal(providing_args=['user', 'post'])
thread_unfollowed = Signal(providing_args=['user', 'post'])
comment_created = Signal(providing_args=['user', 'post'])
comment_edited = Signal(providing_args=['user', 'post'])
comment_voted = Signal(providing_args=['user', 'post'])
comment_deleted = Signal(providing_args=['user', 'post', 'involved_users'])
comment_endorsed = Signal(providing_args=['user', 'post'])


@receiver(post_save, sender=CourseCohortsSettings)
def update_cohorted_discussions(sender, instance, **kwargs):
    from lms.djangoapps.django_comment_client.utils import enrollment_track_group_count
    try:
        course_discussion_settings = CourseDiscussionSettings.objects.get(course_id=instance.course_id)
        division_scheme = course_discussion_settings.division_scheme

        if instance.is_cohorted:
            division_scheme = CourseDiscussionSettings.COHORT
        elif division_scheme == CourseDiscussionSettings.COHORT:
            division_scheme = CourseDiscussionSettings.NONE
        elif (
            division_scheme == CourseDiscussionSettings.ENROLLMENT_TRACK and
            enrollment_track_group_count(course_discussion_settings.course_id) <= 1
        ):
            division_scheme = CourseDiscussionSettings.NONE

        setattr(course_discussion_settings, "division_scheme", division_scheme)
        setattr(course_discussion_settings, "divided_discussions", instance.cohorted_discussions)
        course_discussion_settings.save()

    except CourseDiscussionSettings.DoesNotExist:
        set_course_discussion_settings(
            course_key=instance.course_id,
            divided_discussions=instance.cohorted_discussions,
        )
