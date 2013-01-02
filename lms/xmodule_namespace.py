from xmodule.model import Namespace, Boolean, Scope, String, List
from xmodule.fields import Date, Timedelta


class StringyBoolean(Boolean):
    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        return value


class LmsNamespace(Namespace):
    hide_from_toc = StringyBoolean(
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
        default='',
    )

    display_name = String(
        help="Display name for this module",
        scope=Scope.settings,
        computed_default=lambda module: module.url_name.replace('_', ' ')
    )
    start = Date(help="Start time when this module is visible", scope=Scope.settings)
    due = String(help="Date that this problem is due by", scope=Scope.settings, default='')
    source_file = String(help="DO NOT USE", scope=Scope.settings)
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    ispublic = Boolean(help="Whether this course is open to the public, or only to admins", scope=Scope.settings)
    graceperiod = Timedelta(help="Amount of time after the due date that submissions will be accepted", scope=Scope.settings)
    showanswer = String(help="When to show the problem answer to the student", scope=Scope.settings, default="closed")
    rerandomize = String(help="When to rerandomize the problem", default="always", scope=Scope.settings)

