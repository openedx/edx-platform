"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""


from django.conf import settings
from django.utils.translation import gettext_noop
from xmodule.tabs import TabFragmentViewMixin

import lms.djangoapps.discussion.django_comment_client.utils as utils
from lms.djangoapps.courseware.tabs import EnrolledTab
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration, Provider
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url
from openedx.features.lti_course_tab.tab import DiscussionLtiCourseTab


class DiscussionTab(TabFragmentViewMixin, EnrolledTab):
    """
    A tab for the cs_comments_service forums.
    """

    type = 'discussion'
    title = gettext_noop('Discussion')
    priority = 40
    view_name = 'forum_form_discussion'
    fragment_view_name = 'lms.djangoapps.discussion.views.DiscussionBoardFragmentView'
    is_hideable = settings.FEATURES.get('ALLOW_HIDING_DISCUSSION_TAB', False)
    is_default = False
    body_class = 'discussion'
    online_help_token = 'discussions'

    @classmethod
    def is_enabled(cls, course, user=None):
        if not super().is_enabled(course, user):
            return False
        # Disable the regular discussion tab if LTI-based external Discussion forum is enabled
        if DiscussionLtiCourseTab.is_enabled(course, user):
            return False
        return utils.is_discussion_enabled(course.id)

    @property
    def link_func(self):
        legacy_link_func = super().link_func

        def _link_func(course, reverse_func):
            config = DiscussionsConfiguration.get(course.id)
            if config.provider_type == Provider.OPEN_EDX:
                return get_learning_mfe_home_url(course_key=course.id, url_fragment=self.type)
            else:
                return legacy_link_func(course, reverse_func)
        return _link_func
