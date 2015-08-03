""" API v1 models. """
from itertools import groupby

import logging
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from course_modes.models import CourseMode
from verify_student.models import VerificationDeadline

log = logging.getLogger(__name__)


class Course(object):
    """ Pseudo-course model used to group CourseMode objects. """
    id = None  # pylint: disable=invalid-name
    modes = None
    _deleted_modes = None

    def __init__(self, id, modes, verification_deadline=None):  # pylint: disable=invalid-name,redefined-builtin
        self.id = CourseKey.from_string(unicode(id))  # pylint: disable=invalid-name
        self.modes = list(modes)
        self.verification_deadline = verification_deadline
        self._deleted_modes = []

    @property
    def name(self):
        """ Return course name. """
        course_id = CourseKey.from_string(unicode(self.id))  # pylint: disable=invalid-name

        try:
            return CourseOverview.get_from_id(course_id).display_name
        except CourseOverview.DoesNotExist:
            # NOTE (CCB): Ideally, the course modes table should only contain data for courses that exist in
            # modulestore. If that is not the case, say for local development/testing, carry on without failure.
            log.warning('Failed to retrieve CourseOverview for [%s]. Using empty course name.', course_id)
            return None

    def get_mode_display_name(self, mode):
        """ Returns display name for the given mode. """
        slug = mode.mode_slug.strip().lower()

        if slug == 'credit':
            return 'Credit'
        if 'professional' in slug:
            return 'Professional Education'
        elif slug == 'verified':
            return 'Verified Certificate'
        elif slug == 'honor':
            return 'Honor Certificate'
        elif slug == 'audit':
            return 'Audit'

        return mode.mode_slug

    @transaction.commit_on_success
    def save(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ Save the CourseMode objects to the database. """

        # Update the verification deadline for the course (not the individual modes)
        VerificationDeadline.set_deadline(self.id, self.verification_deadline)

        for mode in self.modes:
            mode.course_id = self.id
            mode.mode_display_name = self.get_mode_display_name(mode)
            mode.save()

        deleted_mode_ids = [mode.id for mode in self._deleted_modes]
        CourseMode.objects.filter(id__in=deleted_mode_ids).delete()
        self._deleted_modes = []

    def update(self, attrs):
        """ Update the model with external data (usually passed via API call). """
        self.verification_deadline = attrs.get('verification_deadline')

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
            merged_mode.expiration_datetime = posted_mode.expiration_datetime

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
            verification_deadline = VerificationDeadline.deadline_for_course(course_id)
            return cls(course_id, list(course_modes), verification_deadline=verification_deadline)

        return None

    @classmethod
    def iterator(cls):
        """ Generator that yields all courses. """
        course_modes = CourseMode.objects.order_by('course_id')

        for course_id, modes in groupby(course_modes, lambda o: o.course_id):
            yield cls(course_id, list(modes))
