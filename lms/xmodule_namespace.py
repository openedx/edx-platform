from xmodule.model import Namespace, Boolean, Scope, String, List
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
        scope=Scope.settings,
    )

    display_name = String(
        help="Display name for this module",
        scope=Scope.settings,
        computed_default=lambda module: module.url_name.replace('_', ' ')
    )
    start = Date(help="Start time when this module is visible", scope=Scope.settings)
    due = String(help="Date that this problem is due by", scope=Scope.settings, default='')
    filename = List(help="DO NOT USE", scope=Scope.content, default=['', None])
    source_file = String(help="DO NOT USE", scope=Scope.settings)
    giturl = String(help="DO NOT USE", scope=Scope.settings, default='https://github.com/MITx')
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    ispublic = Boolean(help="Whether this course is open to the public, or only to admins", scope=Scope.settings)
