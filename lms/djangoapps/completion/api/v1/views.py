""" API v1 views. """
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.db import DatabaseError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError

from lms.djangoapps.completion.models import BlockCompletion
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.lib.api.permissions import IsStaffOrOwner
from student.models import CourseEnrollment
from completion import waffle


class CompletionBatchView(APIView):
    """
    Handles API requests to submit batch completions.
    """
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)
    REQUIRED_KEYS = ['username', 'course_key', 'blocks']

    def _validate_and_parse(self, batch_object):
        """
        Performs validation on the batch object to make sure it is in the proper format.

        Parameters:
            * batch_object: The data provided to a POST. The expected format is the following:
            {
                "username": "username",
                "course_key": "course-key",
                "blocks": {
                    "block_key1": 0.0,
                    "block_key2": 1.0,
                    "block_key3": 1.0,
                }
            }


        Return Value:
            * tuple: (User, CourseKey, List of tuples (UsageKey, completion_float)

        Raises:

            django.core.exceptions.ValidationError:
                If any aspect of validation fails a ValidationError is raised.

            ObjectDoesNotExist:
                If a database object cannot be found an ObjectDoesNotExist is raised.
        """
        if not waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING):
            raise ValidationError(
                _("BlockCompletion.objects.submit_batch_completion should not be called when the feature is disabled.")
            )

        for key in self.REQUIRED_KEYS:
            if key not in batch_object:
                raise ValidationError(_("Key '{key}' not found.".format(key=key)))

        username = batch_object['username']
        user = User.objects.get(username=username)

        course_key = batch_object['course_key']
        try:
            course_key_obj = CourseKey.from_string(course_key)
        except InvalidKeyError:
            raise ValidationError(_("Invalid course key: {}").format(course_key))
        course_structure = CourseStructure.objects.get(course_id=course_key_obj)

        if not CourseEnrollment.is_enrolled(user, course_key_obj):
            raise ValidationError(_('User is not enrolled in course.'))

        blocks = batch_object['blocks']
        block_objs = []
        for block_key in blocks:
            if block_key not in course_structure.structure['blocks'].keys():
                raise ValidationError(_("Block with key: '{key}' is not in course {course}")
                                      .format(key=block_key, course=course_key))

            block_key_obj = UsageKey.from_string(block_key)
            completion = float(blocks[block_key])
            block_objs.append((block_key_obj, completion))

        return user, course_key_obj, block_objs

    def post(self, request, *args, **kwargs):
        """
        Inserts a batch of completions.

        REST Endpoint Format:
        {
          "username": "username",
          "course_key": "course-key",
          "blocks": {
            "block_key1": 0.0,
            "block_key2": 1.0,
            "block_key3": 1.0,
          }
        }

        **Returns**

        A Response object, with an appropriate status code.

        If successful, status code is 200.
        {
           "detail" : _("ok")
        }

        Otherwise, a 400 or 404 may be returned, and the "detail" content will explain the error.

        """
        batch_object = request.data or {}
        try:
            user, course_key, blocks = self._validate_and_parse(batch_object)
            BlockCompletion.objects.submit_batch_completion(user, course_key, blocks)
        except (ValidationError, ValueError) as exc:
            return Response({
                "detail": exc.message,
            }, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as exc:
            return Response({
                "detail": exc.message,
            }, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError as exc:
            return Response({
                "detail": exc.message,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": _("ok")}, status=status.HTTP_200_OK)
