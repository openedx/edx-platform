"""
Mixin class that provides authoring capabilities for XBlocks.
"""


import logging
from typing import Callable

from django.conf import settings
from web_fragments.fragment import Fragment
from xblock.core import XBlock, XBlockMixin
from xblock.fields import String, Scope

log = logging.getLogger(__name__)

VISIBILITY_VIEW = 'visibility_view'


@XBlock.needs("i18n")
@XBlock.needs("mako")
class AuthoringMixin(XBlockMixin):
    """
    Mixin class that provides authoring capabilities for XBlocks.
    """
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
        from cms.djangoapps.contentstore.utils import reverse_course_url
        fragment.add_content(self.runtime.service(self, 'mako').render_cms_template('visibility_editor.html', {
            'xblock': self,
            'manage_groups_url': reverse_course_url('group_configurations_list_handler', self.location.course_key),
        }))
        fragment.add_javascript_url(self._get_studio_resource_url('/js/xblock/authoring.js'))
        fragment.initialize_js('VisibilityEditorInit')
        return fragment

    copied_from_block = String(
        # Note: used by the content_staging app. This field is not needed in the LMS.
        help="ID of the block that this one was copied from, if any. Used when copying and pasting blocks in Studio.",
        scope=Scope.settings,
        enforce_type=True,
    )

    def editor_saved(self, user, old_metadata, old_content) -> None:  # pylint: disable=unused-argument
        """
        Called right *before* the block is written to the DB. Can be used, e.g., to modify fields before saving.

        By default, is a no-op. Can be overriden in subclasses.
        """

    def post_editor_saved(self, user, old_metadata, old_content) -> None:  # pylint: disable=unused-argument
        """
        Called right *after* the block is written to the DB. Can be used, e.g., to spin up followup tasks.

        By default, is a no-op. Can be overriden in subclasses.
        """

    def studio_post_duplicate(
        self,
        source_item,
        store,
        user,
        duplication_function: Callable[..., None],
        shallow: bool,
    ) -> None:  # pylint: disable=unused-argument
        """
        Called when a the block is duplicated. Can be used, e.g., for special handling of child duplication.

        Children must always be handled. In case of inheritance it can be done by running this method with super().

        By default, implements standard duplication logic.
        """
        if not source_item.has_children or shallow:
            return

        self.children = self.children or []
        for child in source_item.children:
            dupe = duplication_function(self.location, child, user=user, is_child=True)
            if dupe not in self.children:  # duplicate_fun may add the child for us.
                self.children.append(dupe)
        store.update_item(self, user.id)
