"""
Tests for StudioEditableModule.
"""

from xmodule.tests.test_vertical import BaseVerticalModuleTest
from xmodule.x_module import AUTHOR_VIEW


class StudioEditableModuleTestCase(BaseVerticalModuleTest):
    def test_render_reorderable_children(self):
        """
        Test the behavior of render_reorderable_children.
        """
        reorderable_items = set()
        context = {
            'reorderable_items': reorderable_items,
            'read_only': False,
            'root_xblock': self.vertical,
        }

        # Both children of the vertical should be rendered as reorderable
        self.module_system.render(self.vertical, AUTHOR_VIEW, context).content  # pylint: disable=expression-not-assigned
        self.assertIn(self.vertical.get_children()[0].location, reorderable_items)
        self.assertIn(self.vertical.get_children()[1].location, reorderable_items)
