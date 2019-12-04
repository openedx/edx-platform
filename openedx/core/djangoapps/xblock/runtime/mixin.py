"""
A mixin that provides functionality and default attributes for all XBlocks in
the new XBlock runtime.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from xblock.core import XBlock, XBlockMixin
from xblock.exceptions import JsonHandlerError


@XBlock.wants('completion')
class LmsBlockMixin(XBlockMixin):
    """
    A mixin that provides functionality and default attributes for all XBlocks
    in the new XBlock runtime.

    These are not standard XBlock attributes but are used by the LMS (and
    possibly Studio).
    """

    # This indicates whether the XBlock has a score (e.g. it's a problem, not
    # static content). If it does, it should set this and provide scoring
    # functionality by inheriting xblock.scorable.ScorableXBlockMixin
    has_score = False

    @XBlock.json_handler
    def publish_completion(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Allow the frontend app that's rendering this XBlock to mark it as
        completed when the user views it, if appropriate.

        Copied from lms.djangoapps.lms_xblock.mixin.LmsBlockMixin
        """
        completion_service = self.runtime.service(self, 'completion')
        if completion_service is None:
            raise JsonHandlerError(500, u"No completion service found")
        elif not completion_service.completion_tracking_enabled():
            raise JsonHandlerError(404, u"Completion tracking is not enabled and API calls are unexpected")
        if not completion_service.can_mark_block_complete_on_view(self):
            raise JsonHandlerError(400, u"Block not configured for completion on view.")
        self.runtime.publish(self, "completion", data)
        return {'result': 'ok'}
