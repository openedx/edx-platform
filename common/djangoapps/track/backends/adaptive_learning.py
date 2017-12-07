""" Event tracker backend that sends relevant data to adaptive learning service. """

from __future__ import absolute_import

from functools import reduce  # pylint: disable=redefined-builtin
import logging
import operator

from opaque_keys.edx.keys import CourseKey, UsageKey

from track.backends import BaseBackend
from xmodule.library_content_module import AdaptiveLibraryContentModule
from xmodule.modulestore.django import modulestore
from xmodule.util.adaptive_learning import AdaptiveLearningConfiguration


log = logging.getLogger(__name__)


class AdaptiveLearningBackend(BaseBackend):
    """
    Event tracker backend for notifying external service that provides adaptive learning features
    about relevant events.
    """

    def __init__(self, store=None, **options):
        """
        Make modulestore available to this backend.
        """
        super(AdaptiveLearningBackend, self).__init__(**options)
        self.modulestore = store or modulestore

    @staticmethod
    def _get_from_event(event, path, default=None):
        """
        Extract value of `path` from `event` dictionary and return it.

        If `path` does not exist in `event`, return `default` value instead.
        """
        path_components = path.split('.')
        try:
            return reduce(operator.getitem, path_components, event)
        except (KeyError, TypeError):
            return default

    def is_problem_check(self, event):
        """
        Return True if `event` is of type `problem_check`, else False.
        """
        return self._get_from_event(event, 'event_type') == 'problem_check'

    def get_course(self, event):
        """
        Retrieve course corresponding to course ID mentioned in `event` from DB
        and return it.
        """
        course_id = self._get_from_event(event, 'context.course_id')
        course_key = CourseKey.from_string(course_id)
        return self.modulestore().get_course(course_key)

    def get_block_id(self, event):
        """
        Return ID of block that `event` belongs to.
        """
        usage_key_string = self._get_from_event(event, 'context.module.usage_key')
        usage_key = UsageKey.from_string(usage_key_string)
        return usage_key.block_id

    def get_user_id(self, event):
        """
        Return ID of user that triggered `event`.
        """
        return self._get_from_event(event, 'context.user_id')

    def get_success(self, event):
        """
        Extract success information from `event`, convert it to format that adaptive learning service expects,
        and return it.
        """
        success = self._get_from_event(event, 'event.success')
        if success == 'correct':
            return '100'
        elif success == 'incorrect':
            return '0'

    def send(self, event):
        """
        Instruct AdaptiveLibraryContentModule to send result event
        to external service that provides adaptive learning features.
        """
        if self.is_problem_check(event):
            course = self.get_course(event)
            if AdaptiveLearningConfiguration.is_meaningful(course.adaptive_learning_configuration):
                block_id = self.get_block_id(event)
                user_id = self.get_user_id(event)
                success = self.get_success(event)
                AdaptiveLibraryContentModule.send_result_event(course, block_id, user_id, success)
