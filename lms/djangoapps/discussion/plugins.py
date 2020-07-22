"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.discussions.discussions_apps import DiscussionApp
from .django_comment_client.utils import is_discussion_enabled


class CommentServiceDiscussionApp(DiscussionApp):
    """
    Discussion Plugin app for cs_comments_service.
    """
    name = "cs_comments"
    friendly_name = _("Inbuilt Discussion Forums")

    capabilities = [

    ]
    course_tab_view = "lms.djangoapps.discussion.views.DiscussionBoardFragmentView"
    course_tab_view_name = "forum_form_discussion"

    @classmethod
    def is_enabled(cls, request=None, context_key=None, user=None):
        return is_discussion_enabled(context_key)
