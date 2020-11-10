"""
Piazza Discussion provider plugin.
"""
from django.utils.translation import ugettext as _
from openedx.core.djangoapps.discussions.discussions_apps import (
    DiscussionApp,
    DiscussionAppCapabilities,
)


class PiazzaDiscussionApp(DiscussionApp):
    """
    Discussion Plugin app for Piazza.
    """
    name = "piazza"
    friendly_name = _("Piazza")

    capabilities = [
        DiscussionAppCapabilities.LTI1p1,
    ]
    course_tab_view = "openedx.features.discussion_provider_piazza.views.PiazzaCourseTabView"
