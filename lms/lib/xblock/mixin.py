"""
Namespace that defines fields common to all blocks used in the LMS
"""
from xblock.fields import Boolean, Scope, String, XBlockMixin


class LmsBlockMixin(XBlockMixin):
    """
    Mixin that defines fields common to all blocks used in the LMS
    """
    hide_from_toc = Boolean(
        help="Whether to display this module in the table of contents",
        default=False,
        scope=Scope.settings
    )
    format = String(
        help="What format this module is in (used for deciding which "
             "grader to apply, and what to show in the TOC)",
        scope=Scope.settings,
    )
    chrome = String(
        help="Which chrome to show. Options: "
             "chromeless -- No chrome"
             "tabs -- just tabs"
             "accordion -- just accordion"
             "tabs,accordion -- Full Chrome",
        scope=Scope.settings,
        default = None,
    )
    default_tab = String(
        help="Override which tab is selected."
             "If not set, courseware tab is shown.",
        scope=Scope.settings,
        default = None,
    )
    source_file = String(help="source file name (eg for latex)", scope=Scope.settings)
    ispublic = Boolean(help="Whether this course is open to the public, or only to admins", scope=Scope.settings)
