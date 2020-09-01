import logging

from crum import get_current_request

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

from lms.djangoapps.course_home_api.utils import is_request_from_learning_mfe
from openedx.core.lib.mobile_utils import is_request_from_mobile_app
from openedx.features.course_experience.utils import dates_banner_should_display

log = logging.getLogger(__name__)


class PersonalizedLearnerScheduleCallToAction:
    CAPA_SUBMIT_DISABLED = 'capa_submit_disabled'
    VERTICAL_BANNER = 'vertical_banner'

    past_due_class_warnings = set()

    def get_ctas(self, xblock, category):
        """
        Return the calls to action associated with the specified category for the given xblock.

        Look at CallToActionService docstring to see what will be returned.
        """
        ctas = []
        request = get_current_request()

        course_key = xblock.scope_ids.usage_id.context_key
        missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, request.user)
        # Not showing in the missed_gated_content case because those learners are not eligible
        # to shift due dates.
        if not missed_deadlines or missed_gated_content:
            return []

        # Some checks to disable PLS calls to action until these environments (mobile and MFE) support them natively
        if request and is_request_from_mobile_app(request):
            return []

        is_learning_mfe = request and is_request_from_learning_mfe(request)
        if category == self.CAPA_SUBMIT_DISABLED:
            # xblock is a capa problem, and the submit button is disabled. Check if it's because of a personalized
            # schedule due date being missed, and if so, we can offer to shift it.
            if self._is_block_shiftable(xblock):
                ctas.append(self._make_reset_deadlines_cta(xblock, is_learning_mfe))

        elif category == self.VERTICAL_BANNER:
            # xblock is a vertical, so we'll check all the problems inside it. If there are any that will show a
            # a "shift dates" CTA under CAPA_SUBMIT_DISABLED, then we'll also show the same CTA as a vertical banner.
            if any(self._is_block_shiftable(item) for item in xblock.get_display_items()):
                ctas.append(self._make_reset_deadlines_cta(xblock, is_learning_mfe))

        return ctas

    @staticmethod
    def _is_block_shiftable(xblock):
        """
        Test if the xblock would be solvable if we were to shift dates.

        Only xblocks with an is_past_due method (e.g. capa and LTI) will be considered possibly shiftable.
        """
        if not hasattr(xblock, 'is_past_due'):
            return False

        if hasattr(xblock, 'attempts') and hasattr(xblock, 'max_attempts'):
            can_attempt = xblock.max_attempts is None or xblock.attempts < xblock.max_attempts
        else:
            can_attempt = True

        if callable(xblock.is_past_due):
            is_past_due = xblock.is_past_due()
        else:
            PersonalizedLearnerScheduleCallToAction._log_past_due_warning(type(xblock).__name__)
            is_past_due = xblock.is_past_due

        return xblock.self_paced and can_attempt and is_past_due

    @staticmethod
    def _log_past_due_warning(name):
        if name in PersonalizedLearnerScheduleCallToAction.past_due_class_warnings:
            return

        log.warning('PersonalizedLearnerScheduleCallToAction has encountered an xblock that defines is_past_due '
                    'as a property. This is supported for now, but may not be in the future. Please change '
                    '%s.is_past_due into a method.', name)
        PersonalizedLearnerScheduleCallToAction.past_due_class_warnings.add(name)

    @staticmethod
    def _make_reset_deadlines_cta(xblock, is_learning_mfe=False):
        from lms.urls import RESET_COURSE_DEADLINES_NAME
        course_key = xblock.scope_ids.usage_id.context_key

        cta_data = {
            'link': reverse(RESET_COURSE_DEADLINES_NAME),
            'link_name': _('Shift due dates'),
            'form_values': {
                'course_id': course_key,
            },
            'description': _('To participate in this assignment, the suggested schedule for your course needs '
                             'updating. Don’t worry, we’ll shift all the due dates for you and you won’t lose '
                             'any of your progress.'),
        }

        if is_learning_mfe:
            cta_data['event_data'] = {
                'event_name': 'post_event',
                'post_data': {
                    'body_params': {
                        'course_id': str(course_key),
                    },
                    'url': '{}{}'.format(settings.LMS_ROOT_URL, reverse('course-experience-reset-course-deadlines')),
                },
            }

        return cta_data
