"""
Mixin class that provides authoring capabilities for XBlocks.
"""

import logging

from xblock.core import XBlock

from xblock.fields import XBlockMixin
from xblock.fragment import Fragment

logger = logging.getLogger(__name__)

VISIBILITY_VIEW = 'visibility_view'


@XBlock.needs("i18n")
class AuthoringMixin(XBlockMixin):
    """
    Mixin class that provides authoring capabilities for XBlocks.
    """
    _services_requested = {
        'i18n': 'need',
    }

    def visibility_view(self, context=None):
        """
        Render the view to manage an xblock's visibility settings in Studio.
        Args:
            context: Not actively used for this view.
        Returns:
            (Fragment): An HTML fragment for editing the visibility of this XBlock.
        """
        fragment = Fragment()
        fragment.add_content(self.system.render_template('visibility_editor.html', {
            'xblock': self,
        }))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_author_view.js'))
        fragment.initialize_js('VisibilityEditorInit')
        return fragment
