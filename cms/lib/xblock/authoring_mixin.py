"""
Mixin class that provides authoring capabilities for XBlocks.
"""


import logging
from datetime import datetime, timezone
from uuid import uuid4

from django.conf import settings
from web_fragments.fragment import Fragment
from xblock.core import XBlock, XBlockMixin
from xblock.fields import String, Scope
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED


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

    def studio_duplicate(
        self,
        parent_usage_key,
        duplicate_source_usage_key,
        user,
        store,
        dest_usage_key=None,
        display_name=None,
        shallow=False,
        is_child=False,
    ):
        """
        Duplicate an existing xblock as a child of the supplied parent_usage_key. You can
        optionally specify what usage key the new duplicate block will use via dest_usage_key.

        If shallow is True, does not copy children.
        """
        from cms.djangoapps.contentstore.utils import gather_block_attributes, load_services_for_studio

        if not dest_usage_key:
            # Change the blockID to be unique.
            dest_usage_key = self.location.replace(name=uuid4().hex)

        category = dest_usage_key.block_type

        duplicate_metadata, asides_to_create = gather_block_attributes(
            self,
            display_name=display_name,
            is_child=is_child,
        )

        dest_block = store.create_item(
            user.id,
            dest_usage_key.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=self.get_explicitly_set_fields_by_scope(Scope.content),
            metadata=duplicate_metadata,
            runtime=self.runtime,
            asides=asides_to_create,
        )

        # Allow an XBlock to do anything fancy it may need to when duplicated from another block.
        load_services_for_studio(self.runtime, user)
        dest_block.studio_post_duplicate(self, store, user, shallow=shallow)
        # pylint: disable=protected-access
        if "detached" not in self.runtime.load_block_type(category)._class_tags:
            parent = store.get_item(parent_usage_key)
            # If source was already a child of the parent, add duplicate immediately afterward.
            # Otherwise, add child to end.
            if self.location in parent.children:
                source_index = parent.children.index(self.location)
                parent.children.insert(source_index + 1, dest_block.location)
            else:
                parent.children.append(dest_block.location)
            store.update_item(parent, user.id)

        # .. event_implemented_name: XBLOCK_DUPLICATED
        XBLOCK_DUPLICATED.send_event(
            time=datetime.now(timezone.utc),
            xblock_info=DuplicatedXBlockData(
                usage_key=dest_block.location,
                block_type=dest_block.location.block_type,
                source_usage_key=duplicate_source_usage_key,
            ),
        )

        return dest_block.location

    def studio_post_duplicate(
        self,
        source_item,
        store,
        user,
        shallow: bool,
    ) -> None:  # pylint: disable=unused-argument
        """
        Called when after a block is duplicated. Can be used, e.g., for special handling of child duplication.

        Children must always be handled. In case of inheritance it can be done by running this method with super().

        By default, implements standard duplication logic.
        """
        if not source_item.has_children or shallow:
            return

        self.children = self.children or []
        for child in source_item.children:
            child_block = store.get_item(child)
            dupe = child_block.studio_duplicate(self.location, child, user=user, store=store, is_child=True)
            if dupe not in self.children:  # studio_duplicate may add the child for us.
                self.children.append(dupe)
        store.update_item(self, user.id)
