"""
Completion tracking and aggregation models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, UsageKeyField
from . import waffle

# pylint: disable=ungrouped-imports
try:
    from django.models import BigAutoField  # Coming in django 1.10
except ImportError:
    from openedx.core.djangolib.fields import BigAutoField
# pylint: enable=ungrouped-imports


def validate_percent(value):
    """
    Verify that the passed value is between 0.0 and 1.0.
    """
    if not 0.0 <= value <= 1.0:
        raise ValidationError(_('{value} must be between 0.0 and 1.0').format(value=value))


def validate_positive_float(value):
    """
    Verifies that the passed in value is greater than 0.
    """
    if value < 0.0:
        raise ValidationError(_('{value} must be larger than 0.').format(value=value))


class CompletionManager(models.Manager):
    """
    A completion manager
    """

    def validate(self, user, course_key, block_key):
        """
        Performs validation

        Parameters:
            * user (django.contrib.auth.models.User):
            * course_key (opaque_keys.edx.keys.CourseKey):
            * block_key (opaque_keys.edx.keys.UsageKey):

        Raises:
            TypeError:
                If the wrong type is passed for the parameters.
        """
        if not isinstance(course_key, CourseKey):
            raise TypeError(
                _("course_key must be an instance of `opaque_keys.edx.keys.CourseKey`.  Got {}".format(
                    type(course_key)
                ))
            )
        if not isinstance(block_key, UsageKey):
            raise TypeError(
                _("block_key must be an instance of `opaque_keys.edx.keys.UsageKey`.  Got {}".format(
                    type(block_key)
                ))
            )
        try:
            block_type = block_key.block_type
        except AttributeError:
            raise TypeError(
                _("block_key must be an instance of `opaque_keys.edx.keys.UsageKey`.  Got {}".format(type(block_key)))
            )

    @staticmethod
    def pre_save(sender, instance, **kwargs):
        """
        Validate all fields before saving to database.
        """
        instance.full_clean()


class BlockCompletionManager(CompletionManager):
    """
    Custom manager for BlockCompletion model.

    Adds submit_completion method.
    """

    def submit_completion(self, user, course_key, block_key, completion):
        """
        Update the completion value for the specified record.

        Parameters:
            * user (django.contrib.auth.models.User): The user for whom the
              completion is being submitted.
            * course_key (opaque_keys.edx.keys.CourseKey): The course in
              which the submitted block is found.
            * block_key (opaque_keys.edx.keys.UsageKey): The block that has had
              its completion changed.
            * completion (float in range [0.0, 1.0]): The fractional completion
              value of the block (0.0 = incomplete, 1.0 = complete).

        Return Value:
            (BlockCompletion, bool): A tuple comprising the created or updated
            BlockCompletion object and a boolean value indicating whether the
            object was newly created by this call.

        Raises:
             TypeError:
                If the wrong type is passed for the parameters.

            RuntimeError:
                If waffle.ENABLE_COMPLETION_TRACKING is not enabled.

            django.core.exceptions.ValidationError:
                If the completion parameter is not between 0.0 and 1.0.

            django.db.DatabaseError:
                If there was a problem getting, creating, or updating the
                BlockCompletion record in the database.

                This will also be a more specific error, as described here:
                https://docs.djangoproject.com/en/1.11/ref/exceptions/#database-exceptions.
                IntegrityError and OperationalError are relatively common
                subclasses.
        """
        if not waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING):
            raise RuntimeError(
                _("BlockCompletionManager.submit_completion should not be called when the feature is disabled.")
            )
        self.validate(user, course_key, block_key)

        obj, is_new = self.get_or_create(
            user=user,
            course_key=course_key,
            block_type=block_key.block_type,
            block_key=block_key,
            defaults={'completion': completion},
        )
        if not is_new and obj.completion != completion:
            obj.completion = completion
            obj.full_clean()
            obj.save()
        return obj, is_new


class AggregateCompletionManager(CompletionManager):
    """
    Custom manager for AggregateCompletion model.
    """

    def submit_completion(self, user, course_key, block_key, aggregation_name, earned, possible):
        """
        Inserts and Updates the completion AggregateCompletion for the specified record.

        Parameters:
            * user (django.contrib.auth.models.User): The user for whom the
              completion is being submitted.
            * course_key (opaque_keys.edx.keys.CourseKey): The course in
              which the submitted block is found.
            * block_key (opaque_keys.edx.keys.UsageKey): The block that has had
              its completion changed.
            * aggregation_name (string): The name of the aggregated blocks.
              This is set by the level that the aggregation
              is occurring. Possible values are "course", "chapter", "sequential", "vertical"
            * earned (float): The positive sum of the fractional completions of all descendant blocks up
              to the value of possible.
            * possible (float): The total sum of the possible completion values of all descendant
              blocks that are visible to the user. This should be a positive integer.

        Return Value:
            (BlockCompletion, bool): A tuple comprising the created or updated
            BlockCompletion object and a boolean value indicating whether the
            object was newly created by this call.

        Raises:
            TypeError:
                If the wrong type is passed for the parameters.

            ValueError:
                If the value of earned is greater than possible.

            django.core.exceptions.ValidationError:
                If earned / possible results in a number that is less than 0 or greater than 1 or any float is
                less than zero.

            RuntimeError:
                If waffle.ENABLE_COMPLETION_AGGREGATION is not enabled.

            django.db.DatabaseError:
                If there was a problem getting, creating, or updating the
                BlockCompletion record in the database.

                This will also be a more specific error, as described here:
                https://docs.djangoproject.com/en/1.11/ref/exceptions/#database-exceptions.
                IntegrityError and OperationalError are relatively common
                subclasses.
        """
        if not waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_AGGREGATION):
            raise RuntimeError(
                _("AggregateCompletionManager.submit_completion should "
                  "not be called when the aggregation feature is disabled.")
            )
        if earned > possible:
            raise ValueError(_('Earned cannot be greater than the possible value.'))
        if possible > 0.0:
            percent = earned / possible
        else:
            percent = 1.0
        self.validate(user, course_key, block_key)

        obj, is_new = self.update_or_create(
            user=user,
            course_key=course_key,
            aggregation_name=aggregation_name,
            block_key=block_key,
            defaults={
                'percent': percent,
                'possible': possible,
                'earned': earned,
            },
        )
        return obj, is_new


class BlockCompletion(TimeStampedModel, models.Model):
    """
    Track completion of completable blocks.

    A completion is unique for each (user, course_key, block_key).

    The block_type field is included separately from the block_key to
    facilitate distinct aggregations of the completion of particular types of
    block.

    The completion value is stored as a float in the range [0.0, 1.0], and all
    calculations are performed on this float, though current practice is to
    only track binary completion, where 1.0 indicates that the block is
    complete, and 0.0 indicates that the block is incomplete.
    """
    id = BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User)
    course_key = CourseKeyField(max_length=255)
    block_key = UsageKeyField(max_length=255)
    block_type = models.CharField(max_length=64)
    completion = models.FloatField(validators=[validate_percent])

    objects = BlockCompletionManager()

    class Meta(object):
        index_together = [
            ('course_key', 'block_type', 'user'),
            ('user', 'course_key', 'modified'),
        ]

        unique_together = [
            ('course_key', 'block_key', 'user')
        ]

    def __unicode__(self):
        return 'BlockCompletion: {username}, {course_key}, {block_key}: {completion}'.format(
            username=self.user.username,
            course_key=self.course_key,
            block_key=self.block_key,
            completion=self.completion,
        )


class AggregateCompletion(TimeStampedModel):
    """
    Aggregators are blocks that contain other blocks, are not themselves completable,
    and are considered complete when all descendant blocks are complete.
    """
    id = BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User)
    course_key = CourseKeyField(max_length=255)
    aggregation_name = models.CharField(max_length=255)
    block_key = UsageKeyField(max_length=255)
    earned = models.FloatField(validators=[validate_positive_float])
    possible = models.FloatField(validators=[validate_positive_float])
    percent = models.FloatField(validators=[validate_percent])

    objects = AggregateCompletionManager()

    class Meta(object):
        index_together = [
            ('user', 'aggregation_name', 'course_key', 'block_key'),
            ('course_key', 'aggregation_name', 'block_key', 'percent'),
        ]

        unique_together = [
            ('course_key', 'block_key', 'user', 'aggregation_name')
        ]

    def __unicode__(self):
        return 'AggregationCompletion: {username}, {course_key}, {block_key}: {percent}'.format(
            username=self.user.username,
            course_key=self.course_key,
            block_key=self.block_key,
            percent=self.percent,
        )


pre_save.connect(
    AggregateCompletionManager.pre_save,
    AggregateCompletion,
    dispatch_uid="completion.models.AggregateCompletion"
)
