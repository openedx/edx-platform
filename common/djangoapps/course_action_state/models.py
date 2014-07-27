from django.contrib.auth.models import User
from django.db import models
from xmodule_django.models import CourseKeyField
from managers import CourseActionStateManager, CourseRerunUIStateManager


class CourseActionState(models.Model):
    """
    A django model for maintaining state data for course actions that take a long time.
    For example: course copying (reruns), import, export, and validation.
    """

    class Meta:
        # For performance reasons, we disable "concrete inheritance", by making the Model base class abstract.
        # With the "abstract base class" inheritance model, tables are only created for derived models, not for
        # the parent classes.  This way, we don't have extra overhead of extra tables and joins that would
        # otherwise happen with the multi-table inheritance model.
        abstract = True

    # FIELDS

    # Created is the time this action was initiated
    created_time = models.DateTimeField(auto_now_add=True)

    # Updated is the last time this entry was modified
    updated_time = models.DateTimeField(auto_now=True)

    # User who initiated the course action
    created_user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        # set on_delete to SET_NULL to prevent this model from being deleted in the event the user is deleted
        on_delete=models.SET_NULL,
        # add a '+' at the end to prevent a backward relation from the User model
        related_name='created_by_user+'
    )

    # User who last updated the course action
    updated_user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        # set on_delete to SET_NULL to prevent this model from being deleted in the event the user is deleted
        on_delete=models.SET_NULL,
        # add a '+' at the end to prevent a backward relation from the User model
        related_name='updated_by_user+'
    )

    # Course that is being acted upon
    course_key = CourseKeyField(max_length=255, db_index=True)

    # Action that is being taken on the course
    action = models.CharField(max_length=100, db_index=True)

    # Current state of the action.
    state = models.CharField(max_length=50)

    # MANAGERS
    objects = CourseActionStateManager()


class CourseActionUIState(CourseActionState):
    """
    An abstract django model that is a sub-class of CourseActionState with additional fields related to UI.
    """
    class Meta:
        # See comment in CourseActionState on disabling "concrete inheritance".
        abstract = True

    # FIELDS

    # Whether or not the status should be displayed to users
    should_display = models.BooleanField()

    # Message related to the status
    message = models.CharField(max_length=1000)


# Rerun courses also need these fields. All rerun course actions will have a row here as well.
class CourseRerunState(CourseActionUIState):
    """
    A concrete django model for maintaining state specifically for the Action Course Reruns.
    """
    # FIELDS
    # No additional fields needed at this time.

    # MANAGERS
    # Override the abstract class' manager with a Rerun-specific manager that inherits from the base class' manager.
    objects = CourseRerunUIStateManager()
