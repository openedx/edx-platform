""" API v1 models. """
from itertools import groupby
import logging

from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode

log = logging.getLogger(__name__)


class Course(object):
    """ Pseudo-course model used to group CourseMode objects. """
    id = None  # pylint: disable=invalid-name
    modes = None
    _deleted_modes = None

    def __init__(self, id, modes):  # pylint: disable=invalid-name,redefined-builtin
        self.id = CourseKey.from_string(unicode(id))  # pylint: disable=invalid-name
        self.modes = list(modes)
        self._deleted_modes = []

    @transaction.commit_on_success
    def save(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ Save the CourseMode objects to the database. """
        for mode in self.modes:
            mode.course_id = self.id
            mode.mode_display_name = mode.mode_slug
            mode.save()

        deleted_mode_ids = [mode.id for mode in self._deleted_modes]
        CourseMode.objects.filter(id__in=deleted_mode_ids).delete()
        self._deleted_modes = []

    def update(self, attrs):
        """ Update the model with external data (usually passed via API call). """
        existing_modes = {mode.mode_slug: mode for mode in self.modes}
        merged_modes = set()
        merged_mode_keys = set()

        for posted_mode in attrs.get('modes', []):
            merged_mode = existing_modes.get(posted_mode.mode_slug, CourseMode())

            merged_mode.course_id = self.id
            merged_mode.mode_slug = posted_mode.mode_slug
            merged_mode.mode_display_name = posted_mode.mode_slug
            merged_mode.min_price = posted_mode.min_price
            merged_mode.currency = posted_mode.currency
            merged_mode.sku = posted_mode.sku

            merged_modes.add(merged_mode)
            merged_mode_keys.add(merged_mode.mode_slug)

        deleted_modes = set(existing_modes.keys()) - merged_mode_keys
        self._deleted_modes = [existing_modes[mode] for mode in deleted_modes]
        self.modes = list(merged_modes)

    @classmethod
    def get(cls, course_id):
        """ Retrieve a single course. """
        try:
            course_id = CourseKey.from_string(unicode(course_id))
        except InvalidKeyError:
            log.debug('[%s] is not a valid course key.', course_id)
            raise ValueError

        course_modes = CourseMode.objects.filter(course_id=course_id)

        if course_modes:
            return cls(unicode(course_id), list(course_modes))

        return None

    @classmethod
    def iterator(cls):
        """ Generator that yields all courses. """
        course_modes = CourseMode.objects.order_by('course_id')

        for course_id, modes in groupby(course_modes, lambda o: o.course_id):
            yield cls(course_id, list(modes))
