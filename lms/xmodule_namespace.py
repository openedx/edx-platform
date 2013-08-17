"""
Namespace that defines fields common to all blocks used in the LMS
"""
from xblock.core import Namespace, Boolean, Scope, String, Float
from xmodule.fields import Date, Timedelta


class LmsNamespace(Namespace):
    """
    Namespace that defines fields common to all blocks used in the LMS
    """
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

    start = Date(help="Start time when this module is visible", scope=Scope.settings)
    due = Date(help="Date that this problem is due by", scope=Scope.settings)
    source_file = String(help="source file name (eg for latex)", scope=Scope.settings)
    giturl = String(help="url root for course data git repository", scope=Scope.settings)
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    ispublic = Boolean(help="Whether this course is open to the public, or only to admins", scope=Scope.settings)
    graceperiod = Timedelta(
        help="Amount of time after the due date that submissions will be accepted",
        scope=Scope.settings
    )
    showanswer = String(help="When to show the problem answer to the student", scope=Scope.settings, default="closed")
    rerandomize = String(help="When to rerandomize the problem", default="always", scope=Scope.settings)
    days_early_for_beta = Float(
        help="Number of days early to show content to beta users",
        default=None,
        scope=Scope.settings
    )
