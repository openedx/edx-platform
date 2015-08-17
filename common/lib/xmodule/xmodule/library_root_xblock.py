"""
'library' XBlock (LibraryRoot)
"""
import logging

from xmodule.studio_editable import StudioEditableModule

from xblock.fields import Scope, String, List, Boolean
from xblock.fragment import Fragment
from xblock.core import XBlock

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class LibraryRoot(XBlock):
    """
    The LibraryRoot is the root XBlock of a content library. All other blocks in
    the library are its children. It contains metadata such as the library's
    display_name.
    """
    display_name = String(
        help=_("Enter the name of the library as it should appear in Studio."),
        default="Library",
        display_name=_("Library Display Name"),
        scope=Scope.settings
    )
    advanced_modules = List(
        display_name=_("Advanced Module List"),
        help=_("Enter the names of the advanced components to use in your library."),
        scope=Scope.settings,
        xml_node=True,
    )
    show_children_previews = Boolean(
        display_name="Hide children preview",
        help="Choose if preview of library contents is shown",
        scope=Scope.user_state,
        default=True
    )
    has_children = True
    has_author_view = True

    def __unicode__(self):
        return u"Library: {}".format(self.display_name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        fragment = Fragment()
        self.render_children(context, fragment, can_reorder=False, can_add=True)
        return fragment

    def render_children(self, context, fragment, can_reorder=False, can_add=False):  # pylint: disable=unused-argument
        """
        Renders the children of the module with HTML appropriate for Studio. Reordering is not supported.
        """
        contents = []

        paging = context.get('paging', None)

        children_count = len(self.children)  # pylint: disable=no-member
        item_start, item_end = 0, children_count

        # TODO sort children
        if paging:
            page_number = paging.get('page_number', 0)
            raw_page_size = paging.get('page_size', None)
            page_size = raw_page_size if raw_page_size is not None else children_count
            item_start, item_end = page_size * page_number, page_size * (page_number + 1)

        children_to_show = self.children[item_start:item_end]  # pylint: disable=no-member

        force_render = context.get('force_render', None)

        for child_key in children_to_show:  # pylint: disable=E1101
            # Children must have a separate context from the library itself. Make a copy.
            child_context = context.copy()
            child_context['show_preview'] = self.show_children_previews
            child_context['can_edit_visibility'] = False
            child = self.runtime.get_block(child_key)
            child_view_name = StudioEditableModule.get_preview_view_name(child)

            if unicode(child.location) == force_render:
                child_context['show_preview'] = True

            if child_context['show_preview']:
                rendered_child = self.runtime.render_child(child, child_view_name, child_context)
            else:
                rendered_child = self.runtime.render_child_placeholder(child, child_view_name, child_context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': unicode(child.location),
                'content': rendered_child.content,
            })

        fragment.add_content(
            self.runtime.render_template("studio_render_paged_children_view.html", {
                'items': contents,
                'xblock_context': context,
                'can_add': can_add,
                'first_displayed': item_start,
                'total_children': children_count,
                'displayed_children': len(children_to_show),
                'previews': self.show_children_previews
            })
        )

    @property
    def display_org_with_default(self):
        """
        Org display names are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'org' field from the key.
        """
        return self.scope_ids.usage_id.course_key.org

    @property
    def display_number_with_default(self):
        """
        Display numbers are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'library' field from the key.
        """
        return self.scope_ids.usage_id.course_key.library

    @XBlock.json_handler
    def trigger_previews(self, request_body, suffix):  # pylint: disable=unused-argument
        """ Enable or disable previews in studio for library children. """
        self.show_children_previews = request_body.get('showChildrenPreviews', self.show_children_previews)
        return {'showChildrenPreviews': self.show_children_previews}
