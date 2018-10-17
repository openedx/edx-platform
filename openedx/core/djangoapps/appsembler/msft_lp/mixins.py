"""
Reusable mixins for XBlocks and/or XModules
"""

from xblock.fields import Scope, String, Float, Boolean, XBlockMixin

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class MsftLPMixin(XBlockMixin):

    # Marks if the course is a Microsft course. This advanced settings only will
    # be available if the feature flag CUSTOMER_IS_MICROSOFT_LEARNING_PARTNER is
    # set to True
    is_microsoft_course = Boolean(
        display_name=_("Is a Microsoft Course"),
        help=_("Set to true if is a microsoft course, so the learners can get access to MSFT certification"),
        default=False,
        scope=Scope.settings)
