"""
Completion tracking and aggregation models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import ugettext as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from opaque_keys.edx.keys import CourseKey

from . import waffle

# pylint: disable=ungrouped-imports
try:
    from django.models import BigAutoField  # New in django 1.10
except ImportError:
    from openedx.core.djangolib.fields import BigAutoField
# pylint: enable=ungrouped-imports


def validate_percent(value):
    """
    Verify that the passed value is between 0.0 and 1.0.
    """
    if not 0.0 <= value <= 1.0:
        raise ValidationError(_('{value} must be between 0.0 and 1.0').format(value=value))


class BlockCompletionManager(models.Manager):
    """
    Custom manager for BlockCompletion model.

    Adds submit_completion and submit_batch_completion methods.
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

            ValueError:
                If the wrong type is passed for one of the parameters.

            django.core.exceptions.ValidationError:
                If a float is passed that is not between 0.0 and 1.0.

            django.db.DatabaseError:
                If there was a problem getting, creating, or updating the
                BlockCompletion record in the database.

                This will also be a more specific error, as described here:
                https://docs.djangoproject.com/en/1.11/ref/exceptions/#database-exceptions.
                IntegrityError and OperationalError are relatively common
                subclasses.
        """

        # Raise ValueError to match normal django semantics for wrong type of field.
        if not isinstance(course_key, CourseKey):
            raise ValueError(
                "course_key must be an instance of `opaque_keys.edx.keys.CourseKey`.  Got {}".format(type(course_key))
            )
        try:
            block_type = block_key.block_type
        except AttributeError:
            raise ValueError(
                "block_key must be an instance of `opaque_keys.edx.keys.UsageKey`.  Got {}".format(type(block_key))
            )

        if waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING):
            obj, is_new = self.get_or_create(
                user=user,
                course_key=course_key,
                block_type=block_type,
                block_key=block_key,
                defaults={'completion': completion},
            )
            if not is_new and obj.completion != completion:
                obj.completion = completion
                obj.full_clean()
                obj.save()
        else:
            # If the feature is not enabled, this method should not be called.  Error out with a RuntimeError.
            raise RuntimeError(
                "BlockCompletion.objects.submit_completion should not be called when the feature is disabled."
            )
        return obj, is_new

    @transaction.atomic()
    def submit_batch_completion(self, user, course_key, blocks):
        """
        Performs a batch insertion of completion objects.

        Parameters:
            * user (django.contrib.auth.models.User): The user for whom the
              completions are being submitted.
            * course_key (opaque_keys.edx.keys.CourseKey): The course in
              which the submitted blocks are found.
            * blocks: A list of tuples of UsageKey to float completion values.
              (float in range [0.0, 1.0]): The fractional completion
              value of the block (0.0 = incomplete, 1.0 = complete).

        Return Value:
            Dict of (BlockCompletion, bool): A dictionary with a
            BlockCompletion object key and a value of bool. The boolean value
            indicates whether the object was newly created by this call.

        Raises:

            ValueError:
                If the wrong type is passed for one of the parameters.

            django.core.exceptions.ValidationError:
                If a float is passed that is not between 0.0 and 1.0.

            django.db.DatabaseError:
                If there was a problem getting, creating, or updating the
                BlockCompletion record in the database.
        """
        block_completions = {}
        for block, completion in blocks:
            (block_completion, is_new) = self.submit_completion(user, course_key, block, completion)
            block_completions[block_completion] = is_new
        return block_completions


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

    # note: this usage key may not have the run filled in for
    # old mongo courses.  Use the full_block_key property
    # instead when you want to use/compare the usage_key.
    block_key = UsageKeyField(max_length=255)
    block_type = models.CharField(max_length=64)
    completion = models.FloatField(validators=[validate_percent])

    objects = BlockCompletionManager()

    @property
    def full_block_key(self):
        """
        Returns the "correct" usage key value with the run filled in.
        """
        if self.block_key.run is None:
            return self.block_key.replace(course_key=self.course_key)  # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
        else:
            return self.block_key

    @classmethod
    def get_course_completions(cls, user, course_key):
        """
        query all completions for course/user pair

        Return value:
            dict[BlockKey] = float
        """
        course_block_completions = cls.objects.filter(
            user=user,
            course_key=course_key,
        )
        # will not return if <= 0.0
        return {completion.block_key: completion.completion for completion in course_block_completions}

    @classmethod
    def get_latest_block_completed(cls, user, course_key):
        """
        query latest completion for course/user pair

        Return value:
            obj: block completion
        """
        try:
            latest_modified_block_completion = cls.objects.filter(
                user=user,
                course_key=course_key,
            ).latest()
        except cls.DoesNotExist:
            return
        return latest_modified_block_completion

    class Meta(object):
        index_together = [
            ('course_key', 'block_type', 'user'),
            ('user', 'course_key', 'modified'),
        ]

        unique_together = [
            ('course_key', 'block_key', 'user')
        ]
        get_latest_by = 'modified'

    def __unicode__(self):
        return 'BlockCompletion: {username}, {course_key}, {block_key}: {completion}'.format(
            username=self.user.username,
            course_key=self.course_key,
            block_key=self.block_key,
            completion=self.completion,
        )
