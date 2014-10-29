"""
'library' XBlock (LibraryRoot)
"""
import logging

from .studio_editable import StudioEditableModule
from xblock.core import XBlock
from xblock.fields import Scope, String, List
from xblock.fragment import Fragment

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
        scope=Scope.settings
    )
    has_children = True
    has_author_view = True

    def __unicode__(self):
        return u"Library: {}".format(self.display_name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def author_view(self, context):
        """
        Renders the Studio preview view, which supports drag and drop.
        """
        fragment = Fragment()
        contents = []

        for child_key in self.children:  # pylint: disable=E1101
            context['reorderable_items'].add(child_key)
            child = self.runtime.get_block(child_key)
            rendered_child = self.runtime.render_child(child, StudioEditableModule.get_preview_view_name(child), context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': unicode(child_key),
                'content': rendered_child.content,
            })

        fragment.add_content(self.runtime.render_template("studio_render_children_view.html", {
            'items': contents,
            'xblock_context': context,
            'can_add': True,
            'can_reorder': True,
        }))
        return fragment

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

    @classmethod
    def parse_xml(cls, xml_data, system, id_generator, **kwargs):
        """ XML support not yet implemented. """
        raise NotImplementedError

    def add_xml_to_node(self, resource_fs):
        """ XML support not yet implemented. """
        raise NotImplementedError
