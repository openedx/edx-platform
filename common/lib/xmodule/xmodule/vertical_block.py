"""
VerticalBlock - an XBlock which renders its children in a column.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import copy
import logging

from lxml import etree
from opaque_keys.edx.keys import UsageKey
import six
from web_fragments.fragment import Fragment
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError


from xmodule.mako_module import MakoTemplateBlockBase
from xmodule.progress import Progress
from xmodule.seq_module import SequenceFields
from xmodule.studio_editable import StudioEditableBlock
from xmodule.x_module import STUDENT_VIEW, XModuleFields
from xmodule.xml_module import XmlParserMixin

import webpack_loader.utils

log = logging.getLogger(__name__)

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
CLASS_PRIORITY = ['video', 'problem']


def is_completable_by_viewing(block):
    """
    Returns True if the block can by completed by viewing it.

    This is true of any non-customized, non-scorable, completable block.
    """
    return (
        getattr(block, 'completion_mode', XBlockCompletionMode.COMPLETABLE) == XBlockCompletionMode.COMPLETABLE
        and not getattr(block, 'has_custom_completion', False)
        and not block.has_score
    )


@XBlock.needs('user', 'bookmarks')
@XBlock.wants('completion')
class VerticalBlock(SequenceFields, XModuleFields, StudioEditableBlock, XmlParserMixin, MakoTemplateBlockBase, XBlock):
    """
    Layout XBlock for rendering subblocks vertically.
    """

    resources_dir = 'assets/vertical'

    mako_template = 'widgets/sequence-edit.html'
    js_module_name = "VerticalBlock"

    has_children = True

    show_in_read_only_mode = True

    def get_completable_by_viewing(self, completion_service):
        """
        Return a set of descendent blocks that this vertical still needs to
        mark complete upon viewing.

        Completed blocks are excluded to reduce network traffic from clients.
        """
        if completion_service is None:
            return set()
        if not completion_service.completion_tracking_enabled():
            return set()
        # pylint: disable=no-member
        blocks = {block.location for block in self.get_display_items() if is_completable_by_viewing(block)}
        # pylint: enable=no-member

        # Exclude completed blocks to reduce traffic from client.
        completions = completion_service.get_completions(blocks)
        return {six.text_type(block_key) for block_key in blocks if completions[block_key] < 1.0}

    def get_completion_delay_ms(self, completion_service):
        """
        Do not mark blocks as complete until they have been visible to the user
        for the returned amount of time (in milliseconds).
        """
        if completion_service is None:
            return 0
        return completion_service.get_completion_by_viewing_delay_ms()

    def student_view(self, context):
        """
        Renders the student view of the block in the LMS.
        """
        fragment = Fragment()
        contents = []

        if context:
            child_context = copy(context)
        else:
            child_context = {}

        if 'bookmarked' not in child_context:
            bookmarks_service = self.runtime.service(self, 'bookmarks')
            child_context['bookmarked'] = bookmarks_service.is_bookmarked(usage_key=self.location),  # pylint: disable=no-member
        if 'username' not in child_context:
            user_service = self.runtime.service(self, 'user')
            child_context['username'] = user_service.get_current_user().opt_attrs['edx-platform.username']

        completion_service = self.runtime.service(self, 'completion')

        child_context['child_of_vertical'] = True
        is_child_of_vertical = context.get('child_of_vertical', False)

        # pylint: disable=no-member
        for child in self.get_display_items():
            rendered_child = child.render(STUDENT_VIEW, child_context)
            fragment.add_fragment_resources(rendered_child)

            contents.append({
                'id': six.text_type(child.location),
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
            'unit_title': self.display_name_with_default if not is_child_of_vertical else None,
            'show_bookmark_button': child_context.get('show_bookmark_button', not is_child_of_vertical),
            'bookmarked': child_context['bookmarked'],
            'bookmark_id': u"{},{}".format(child_context['username'], unicode(self.location)),  # pylint: disable=no-member
            'watched_completable_blocks': self.get_completable_by_viewing(completion_service),
            'completion_delay_ms': self.get_completion_delay_ms(completion_service),
        }))

        for tag in webpack_loader.utils.get_as_tags('VerticalStudentView'):
            fragment.add_resource(tag, mimetype='text/html', placement='head')
        fragment.initialize_js('VerticalStudentView')

        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview view, which supports drag and drop.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location  # pylint: disable=no-member

        # For the container page we want the full drag-and-drop, but for unit pages we want
        # a more concise version that appears alongside the "View =>" link-- unless it is
        # the unit page and the vertical being rendered is itself the unit vertical (is_root == True).
        if is_root or not context.get('is_unit_page'):
            self.render_children(context, fragment, can_reorder=True, can_add=True)
        return fragment

    def get_progress(self):
        """
        Returns the progress on this block and all children.
        """
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress

    def get_icon_class(self):
        """
        Returns the highest priority icon class.
        """
        child_classes = set(child.get_icon_class() for child in self.get_children())
        new_class = 'other'
        for higher_class in CLASS_PRIORITY:
            if higher_class in child_classes:
                new_class = higher_class
        return new_class

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                child_block = system.process_xml(etree.tostring(child, encoding='unicode'))
                children.append(child_block.scope_ids.usage_id)
            except Exception as exc:  # pylint: disable=broad-except
                log.exception("Unable to load child when parsing Vertical. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker(u"ERROR: {0}".format(exc))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('vertical')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    @property
    def non_editable_metadata_fields(self):
        """
        Gather all fields which can't be edited.
        """
        non_editable_fields = super(VerticalBlock, self).non_editable_metadata_fields
        non_editable_fields.extend([
            self.fields['due'],
        ])
        return non_editable_fields

    def studio_view(self, context):
        fragment = super(VerticalBlock, self).studio_view(context)
        # This continues to use the old XModuleDescriptor javascript code to enabled studio editing.
        # TODO: Remove this when studio better supports editing of pure XBlocks.
        fragment.add_javascript('VerticalBlock = XModule.Descriptor;')
        return fragment

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing.
        """
        # return key/value fields in a Python dict object
        # values may be numeric / string or dict
        # default implementation is an empty dict
        xblock_body = super(VerticalBlock, self).index_dictionary()
        index_body = {
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(index_body)
        else:
            xblock_body["content"] = index_body
        # We use "Sequence" for sequentials and verticals
        xblock_body["content_type"] = "Sequence"

        return xblock_body

    def find_descendent(self, block_key):
        """
        Return the descendent block with the given block key if it exists.

        Otherwise return None.
        """
        for block in self.get_display_items():  # pylint: disable=no-member
            if block.location == block_key:
                return block

    @XBlock.json_handler
    def publish_completion(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Publish data from the front end.
        """
        block_key = UsageKey.from_string(data.pop('block_key')).map_into_course(self.course_id)
        block = self.find_descendent(block_key)
        if block is None:
            message = "Invalid block: {} not found in {}"
            raise JsonHandlerError(400, message.format(block_key, self.location))  # pylint: disable=no-member
        elif not is_completable_by_viewing(block):
            message = "Invalid block type: {} in block {} not configured for completion by viewing"
            raise JsonHandlerError(400, message.format(type(block), block_key))
        self.runtime.publish(block, "completion", data)
        return {'result': 'ok'}
