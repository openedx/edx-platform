# -*- coding: utf-8 -*-
"""
Mixins for completion.
"""


class CompletionOnViewMixin(object):
    """
    Methods for testing completion on view.
    """

    def xblock_components_mark_completed_on_view_value(self):
        """
        Return the xblock components data-mark-completed-on-view-after-delay value.
        """
        return self.q(css=self.xblock_component_selector).attrs('data-mark-completed-on-view-after-delay')

    def wait_for_xblock_component_to_be_marked_completed_on_view(self, index=0):
        """
        Wait for xblock component to be marked completed on view.

        Arguments
            index (int): index of block to wait on. (default is 0)
        """
        self.wait_for(lambda: (self.xblock_components_mark_completed_on_view_value()[index] == '0'),
                      'Waiting for xblock to be marked completed on view.')
