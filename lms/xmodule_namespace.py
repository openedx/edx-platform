from xmodule.model import Namespace, Boolean, Scope, String
from xmodule.x_module import Date

class LmsNamespace(Namespace):
    hide_from_toc = Boolean(
        help="Whether to display this module in the table of contents",
        default=False,
        scope=Scope.settings
    )
    graded = Boolean(
        help="Whether this module contributes to the final course grade",
        default=False,
        scope=Scope.settings
    )
    format = String(
        help="What format this module is in (used for deciding which "
             "grader to apply, and what to show in the TOC)",
        scope=Scope.settings
    )

    display_name = String(help="Display name for this module", scope=Scope.settings)
    start = Date(help="Start time when this module is visible", scope=Scope.settings)
    due = String(help="Date that this problem is due by", scope=Scope.settings, default='')
