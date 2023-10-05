"""
Module contains various XModule/XBlock services
"""


import inspect
import logging
from functools import partial
from datetime import datetime

from pytz import UTC

from config_models.models import ConfigurationModel
from django.conf import settings
from eventtracking import tracker
from edx_when.field_data import DateLookupFieldData
from xblock.reference.plugins import Service
from xblock.runtime import KvsFieldData

from common.djangoapps.track import contexts
from lms.djangoapps.courseware.masquerade import is_masquerading_as_specific_student
from xmodule.modulestore.django import modulestore
from xmodule.graders import ShowCorrectness, ShowAnswer

from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from lms.djangoapps.courseware.model_data import DjangoKeyValueStore, FieldDataCache
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig

from lms.djangoapps.grades.signals import signals as grades_signals

log = logging.getLogger(__name__)


class SettingsService:
    """
    Allows server-wide configuration of XBlocks on a per-type basis

    XBlock settings are read from XBLOCK_SETTINGS settings key. Each XBlock is allowed access
    to single settings bucket. Bucket is determined by this service using the following rules:

    * Value of SettingsService.xblock_settings_bucket_selector is examined. If XBlock have attribute/property
    with the name of that value this attribute/property is read to get the bucket key (e.g. if XBlock have
    `block_settings_key = 'my_block_settings'`, bucket key would be 'my_block_settings').
    * Otherwise, XBlock class name is used

    Service is content-agnostic: it just returns whatever happen to be in the settings bucket (technically, it returns
    the bucket itself).

    If `default` argument is specified it is returned if:
    * There are no XBLOCK_SETTINGS setting
    * XBLOCK_SETTINGS is empty
    * XBLOCK_SETTINGS does not contain settings bucket

    If `default` is not specified or None, empty dictionary is used for default.

    Example:

        "XBLOCK_SETTINGS": {
            "my_block": {
                "setting1": 1,
                "setting2": []
            },
            "my_other_block": [1, 2, 3],
            "MyThirdBlock": "QWERTY"
        }

        class MyBlock:      block_settings_key='my_block'
        class MyOtherBlock: block_settings_key='my_other_block'
        class MyThirdBlock: pass
        class MissingBlock: pass

        service = SettingsService()
        service.get_settings_bucket(MyBlock())                      # { "setting1": 1, "setting2": [] }
        service.get_settings_bucket(MyOtherBlock())                 # [1, 2, 3]
        service.get_settings_bucket(MyThirdBlock())                 # "QWERTY"
        service.get_settings_bucket(MissingBlock())                 # {}
        service.get_settings_bucket(MissingBlock(), "default")      # "default"
        service.get_settings_bucket(MissingBlock(), None)           # {}
    """
    xblock_settings_bucket_selector = 'block_settings_key'

    def get_settings_bucket(self, block, default=None):
        """ Gets xblock settings dictionary from settings. """
        if not block:
            raise ValueError(f"Expected XBlock instance, got {block} of type {type(block)}")

        actual_default = default if default is not None else {}
        xblock_settings_bucket = getattr(block, self.xblock_settings_bucket_selector, block.unmixed_class.__name__)
        xblock_settings = settings.XBLOCK_SETTINGS if hasattr(settings, "XBLOCK_SETTINGS") else {}
        return xblock_settings.get(xblock_settings_bucket, actual_default)


# TODO: ConfigurationService and its usage will be removed as a part of EDUCATOR-121
# reference: https://openedx.atlassian.net/browse/EDUCATOR-121
class ConfigurationService:
    """
    An XBlock service to talk with the Configuration Models. This service should provide
    a pathway to Configuration Model which is designed to configure the corresponding XBlock.
    """
    def __init__(self, configuration_model):
        """
        Class initializer, this exposes configuration model to XBlock.

        Arguments:
            configuration_model (ConfigurationModel): configurations for an XBlock

        Raises:
            exception (ValueError): when configuration_model is not a subclass of
            ConfigurationModel.
        """
        if not (inspect.isclass(configuration_model) and issubclass(configuration_model, ConfigurationModel)):
            raise ValueError(
                "Expected ConfigurationModel got {} of type {}".format(
                    configuration_model,
                    type(configuration_model)
                )
            )

        self.configuration = configuration_model


class TeamsConfigurationService:
    """
    An XBlock service that returns the teams_configuration object for a course.
    """
    def __init__(self):
        self._course = None

    def get_course(self, course_id):
        """
        Return the course instance associated with this TeamsConfigurationService.
        This default implementation looks up the course from the modulestore.
        """
        return modulestore().get_course(course_id)

    def get_teams_configuration(self, course_id):
        """
        Returns the team configuration for a given course.id
        """
        if not self._course:
            self._course = self.get_course(course_id)
        return self._course.teams_configuration


class RebindUserServiceError(Exception):
    pass


class RebindUserService(Service):
    """
    An XBlock Service that allows modules to get rebound to real users if it was previously bound to an AnonymousUser.

    This used to be a local function inside the `lms.djangoapps.courseware.block_render.prepare_runtime_for_user`
    method. This has been refactored out into a service and lives in this module temporarily.

    TODO: Only the old LTI XBlock uses it in 2 places for LTI 2.0 integration. As the LTI XBlock is deprecated in
    favour of the LTI Consumer XBlock, this should be removed when the LTI XBlock is removed.

    Arguments:
        user (User) - A Django User object
        course_id (str) - Course ID
        course (Course) - Course Object
        kwargs (dict) - all the keyword arguments that need to be passed to the `prepare_runtime_for_user`
            function when it is called during rebinding
    """
    def __init__(self, user, course_id, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.course_id = course_id
        self._kwargs = kwargs

    def rebind_noauth_module_to_user(self, block, real_user):
        """
        Function that rebinds the module to the real_user.

        Will only work within a module bound to an AnonymousUser, e.g. one that's instantiated by the noauth_handler.

        Arguments:
            block (any xblock type):  the module to rebind
            real_user (django.contrib.auth.models.User):  the user to bind to

        Returns:
            nothing (but the side effect is that module is re-bound to real_user)
        """
        if self.user.is_authenticated:
            err_msg = "rebind_noauth_module_to_user can only be called from a module bound to an anonymous user"
            log.error(err_msg)
            raise RebindUserServiceError(err_msg)

        field_data_cache_real_user = FieldDataCache.cache_for_block_descendents(
            self.course_id,
            real_user,
            block,
            asides=XBlockAsidesConfig.possible_asides(),
        )
        student_data_real_user = KvsFieldData(DjangoKeyValueStore(field_data_cache_real_user))

        with modulestore().bulk_operations(self.course_id):
            course = modulestore().get_course(course_key=self.course_id)

        from lms.djangoapps.courseware.block_render import prepare_runtime_for_user
        prepare_runtime_for_user(
            user=real_user,
            student_data=student_data_real_user,  # These have implicit user bindings, rest of args considered not to
            runtime=block.runtime,
            course_id=self.course_id,
            course=course,
            **self._kwargs
        )

        block.bind_for_student(
            real_user.id,
            [
                partial(DateLookupFieldData, course_id=self.course_id, user=self.user),
                partial(OverrideFieldData.wrap, real_user, course),
                partial(LmsFieldData, student_data=student_data_real_user),
            ],
        )


class EventPublishingService(Service):
    """
    An XBlock Service that allows XModules to publish events (e.g. grading, completion).

    We have implemented it as a seperate service to be able to alter its behavior when using
    a different context: LMS, Studio, or Instructor tasks.
    """
    def __init__(self, user, course_id, track_function, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.course_id = course_id
        self.track_function = track_function
        self.completion_service = None

    def publish(self, block, event_type, event):
        """
        A function that allows XModules to publish events.
        """
        self.completion_service = block.runtime.service(block, 'completion')

        handle_event = self._get_event_handler(event_type)
        if handle_event and not is_masquerading_as_specific_student(self.user, self.course_id):
            handle_event(block, event)
        else:
            context = contexts.course_context_from_course_id(self.course_id)
            if not self.user.is_anonymous:
                context['user_id'] = self.user.id

            context['asides'] = {}
            for aside in block.runtime.get_asides(block):
                if hasattr(aside, 'get_event_context'):
                    aside_event_info = aside.get_event_context(event_type, event)
                    if aside_event_info is not None:
                        context['asides'][aside.scope_ids.block_type] = aside_event_info
            with tracker.get_tracker().context(event_type, context):
                self.track_function(event_type, event)

    def _get_event_handler(self, event_type):
        """
        Return an appropriate function to handle the event.

        Returns None if no special processing is required.
        """
        handlers = {
            'grade': self._handle_grade_event,
        }
        if self.completion_service and self.completion_service.completion_tracking_enabled():
            handlers.update(
                {
                    'completion': lambda block, event: self.completion_service.submit_completion(
                        block.scope_ids.usage_id, event['completion']
                    ),
                    'progress': self._handle_deprecated_progress_event,
                }
            )
        return handlers.get(event_type)

    def _handle_grade_event(self, block, event):
        """
        Submit a grade for the block.
        """
        if not self.user.is_anonymous:
            grades_signals.SCORE_PUBLISHED.send(
                sender=None,
                block=block,
                user=self.user,
                raw_earned=event['value'],
                raw_possible=event['max_value'],
                only_if_higher=event.get('only_if_higher'),
                score_deleted=event.get('score_deleted'),
                grader_response=event.get('grader_response'),
            )

    def _handle_deprecated_progress_event(self, block, event):
        """
        DEPRECATED: Submit a completion for the block represented by the
        progress event.

        This exists to support the legacy progress extension used by
        edx-solutions.  New XBlocks should not emit these events, but instead
        emit completion events directly.
        """
        requested_user_id = event.get('user_id', self.user.id)
        if requested_user_id != self.user.id:
            log.warning(f"{self.user} tried to submit a completion on behalf of {requested_user_id}")
            return

        # If blocks explicitly declare support for the new completion API,
        # we expect them to emit 'completion' events,
        # and we ignore the deprecated 'progress' events
        # in order to avoid duplicate work and possibly conflicting semantics.
        if not getattr(block, 'has_custom_completion', False):
            self.completion_service.submit_completion(block.scope_ids.usage_id, 1.0)


class ProblemFeedbackService(Service):
    """
    An XBlock Service that allows XModules to define:

    - if the answers are visible
    - whether correctness is currently hidden. When correctness is hidden, this
    limits the user's access to the correct/incorrect flags, messages, problem
    scores, and aggregate subsection and course grades.
    """
    def __init__(self, block=None, user_is_staff=False, **kwargs):
        super().__init__(**kwargs)
        self._user_is_staff = user_is_staff
        # This is needed because the `Service` class initialization expects the XBlock passed as an `xblock` keyword
        #  argument, but the `service` method from the `DescriptorSystem` passes a `block`.
        self._xblock = self.xblock() or block

    def is_past_due(self):
        """
        Returns if the problem is past its due date.
        """
        if self._xblock:
            return (self._xblock.close_date is not None and
                    datetime.now(UTC) > self._xblock.close_date)
        return False

    def is_attempted(self):
        """
        Has the problem been attempted?
        """
        if self._xblock:
            return self._xblock.attempts > 0
        return False

    def used_all_attempts(self):
        """ All attempts have been used """
        if self._xblock:
            return (self._xblock.max_attempts is not None and
                    self._xblock.attempts >= self._xblock.max_attempts)
        return False

    def closed(self):
        """
        Is the student still allowed to submit answers?
        """
        if self.used_all_attempts():
            return True
        if self.is_past_due():
            return True
        return False

    def answer_available(self):
        """
        Returns whether correctness is available now, for the given attributes.
        """
        if self._xblock:
            show_correctness = self._xblock.show_correctness
            show_answer = self._xblock.showanswer
            max_attempts = self._xblock.max_attempts
            attempts = self._xblock.attempts
            is_correct = self._xblock.is_correct()
            required_attempts = self._xblock.attempts_before_showanswer_button
        else:
            show_correctness = ''
            show_answer = ''
            max_attempts = 0
            attempts = 0
            required_attempts = 0
            is_correct = False
        past_due = self.is_past_due()
        is_attempted = self.is_attempted()
        used_all_attempts = self.used_all_attempts()
        closed = self.closed()

        if not show_correctness:
            # If correctness is being withheld, then don't show answers either.
            return False
        elif show_correctness == ShowCorrectness.NEVER:
            # If correctness is being hidden the answer is not shown
            return False
        elif show_answer == ShowAnswer.NEVER:
            return False
        elif self._user_is_staff:
            # This is after the 'never' check because course staff can see correctness
            # unless the sequence/problem explicitly prevents it
            return True
        elif show_answer == ShowAnswer.ATTEMPTED:
            return is_attempted or past_due
        elif show_answer == ShowAnswer.ANSWERED:
            # NOTE: this is slightly different from 'attempted' -- resetting the problems
            # makes lcp.done False, but leaves attempts unchanged.
            return is_correct
        elif show_answer == ShowAnswer.CLOSED:
            return closed
        elif show_answer == ShowAnswer.FINISHED:
            return closed or is_correct
        elif show_answer == ShowAnswer.CORRECT_OR_PAST_DUE:
            return is_correct or past_due
        elif show_answer == ShowAnswer.PAST_DUE:
            return past_due
        elif show_answer == ShowAnswer.AFTER_SOME_NUMBER_OF_ATTEMPTS:
            if max_attempts and required_attempts >= max_attempts:
                required_attempts = max_attempts
            return attempts >= required_attempts
        elif show_answer == ShowAnswer.ALWAYS:
            return True
        elif show_answer == ShowAnswer.AFTER_ALL_ATTEMPTS:
            return used_all_attempts
        elif show_answer == ShowAnswer.AFTER_ALL_ATTEMPTS_OR_CORRECT:
            return used_all_attempts or is_correct
        elif show_answer == ShowAnswer.ATTEMPTED_NO_PAST_DUE:
            return is_attempted
        return False

    def correctness_available(self):
        """
        Returns whether correctness is available now, for the given attributes.
        """
        if self._xblock:
            due_date = self._xblock.due
            show_correctness = self._xblock.show_correctness
        else:
            due_date = None
            show_correctness = ''

        if show_correctness == ShowCorrectness.NEVER:
            return False
        elif self._user_is_staff:
            # This is after the 'never' check because course staff can see correctness
            # unless the sequence/problem explicitly prevents it
            return True
        elif show_correctness == ShowCorrectness.PAST_DUE:
            # Is it now past the due date?
            return (due_date is None or
                    due_date < datetime.now(UTC))
        return True
