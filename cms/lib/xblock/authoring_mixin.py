"""
Mixin class that provides authoring capabilities for XBlocks.
"""

import logging

from django.conf import settings

from xblock.core import XBlock
from xblock.fields import XBlockMixin
from xblock.fragment import Fragment

log = logging.getLogger(__name__)

VISIBILITY_VIEW = 'visibility_view'


@XBlock.needs("i18n")
class AuthoringMixin(XBlockMixin):
    """
    Mixin class that provides authoring capabilities for XBlocks.
    """
    _services_requested = {
        'i18n': 'need',
    }

    def _get_studio_resource_url(self, relative_url):
        """
        Returns the Studio URL to a static resource.
        """
        return settings.STATIC_URL + relative_url

    def visibility_view(self, _context=None):
        """
        Render the view to manage an xblock's visibility settings in Studio.
        Args:
            _context: Not actively used for this view.
        Returns:
            (Fragment): An HTML fragment for editing the visibility of this XBlock.
        """
        fragment = Fragment()
        from contentstore.utils import reverse_course_url
        fragment.add_content(self.system.render_template('visibility_editor.html', {
            'xblock': self,
            'manage_groups_url': reverse_course_url('group_configurations_list_handler', self.location.course_key),
        }))
        fragment.add_javascript_url(self._get_studio_resource_url('/js/xblock/authoring.js'))
        fragment.initialize_js('VisibilityEditorInit')
        return fragment
