from django.urls import reverse
from django.utils.translation import gettext as _


class PersonalizedLearnerScheduleCallToAction:
    CAPA_SUBMIT_DISABLED = 'capa_submit_disabled'
    VERTICAL_BANNER = 'vertical_banner'

    def get_ctas(self, xblock, category):
        """
        Return the calls to action associated with the specified category for the given xblock.

        See the CallToActionService class constants for a list of recognized categories.

        Returns: list of dictionaries, describing the calls to action, with the following keys:
                 link, link_name, form_values, and description.
                 If the category is not recognized, an empty list is returned.

        An example of a returned list:
        [{
            'link': 'localhost:18000/skip',
            'link_name': 'Skip this Problem',
            'form_values': {
                'foo': 'bar',
            },
            'description': "If you don't want to do this problem, just skip it!"
        }]
        """
        ctas = []

        if category == self.CAPA_SUBMIT_DISABLED:
            # xblock is a capa problem, and the submit button is disabled. Check if it's because of a personalized
            # schedule due date being missed, and if so, we can offer to shift it.
            if self._is_block_shiftable(xblock):
                ctas.append(self._make_reset_deadlines_cta(xblock))

        elif category == self.VERTICAL_BANNER:
            # xblock is a vertical, so we'll check all the problems inside it. If there are any that will show a
            # a "shift dates" CTA under CAPA_SUBMIT_DISABLED, then we'll also show the same CTA as a vertical banner.
            if any(self._is_block_shiftable(item) for item in xblock.get_display_items()):
                ctas.append(self._make_reset_deadlines_cta(xblock))

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

        return xblock.self_paced and can_attempt and xblock.is_past_due()

    @staticmethod
    def _make_reset_deadlines_cta(xblock):
        from lms.urls import RESET_COURSE_DEADLINES_NAME
        return {
            'link': reverse(RESET_COURSE_DEADLINES_NAME),
            'link_name': _('Shift due dates'),
            'form_values': {
                'course_id': xblock.scope_ids.usage_id.context_key,
            },
            'description': _('To participate in this assignment, the suggested schedule for your course needs '
                             'updating. Don’t worry, we’ll shift all the due dates for you and you won’t lose '
                             'any of your progress.'),
        }
