"""
xModule implementation of a learning sequence
"""

# pylint: disable=abstract-method
import collections
import json
import logging
from pkg_resources import resource_string

from lxml import etree
from xblock.core import XBlock
from xblock.fields import Integer, Scope, Boolean, String
from xblock.fragment import Fragment
import newrelic.agent

from .exceptions import NotFoundError
from .fields import Date
from .mako_module import MakoModuleDescriptor
from .progress import Progress
from .x_module import XModule, STUDENT_VIEW
from .xml_module import XmlDescriptor

log = logging.getLogger(__name__)

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class SequenceFields(object):
    has_children = True

    # NOTE: Position is 1-indexed.  This is silly, but there are now student
    # positions saved on prod, so it's not easy to fix.
    position = Integer(help="Last tab viewed in this sequence", scope=Scope.user_state)
    due = Date(
        display_name=_("Due Date"),
        help=_("Enter the date by which problems are due."),
        scope=Scope.settings,
    )

    # Entrance Exam flag -- see cms/contentstore/views/entrance_exam.py for usage
    is_entrance_exam = Boolean(
        display_name=_("Is Entrance Exam"),
        help=_(
            "Tag this course module as an Entrance Exam. "
            "Note, you must enable Entrance Exams for this course setting to take effect."
        ),
        default=False,
        scope=Scope.settings,
    )


class ProctoringFields(object):
    """
    Fields that are specific to Proctored or Timed Exams
    """
    is_time_limited = Boolean(
        display_name=_("Is Time Limited"),
        help=_(
            "This setting indicates whether students have a limited time"
            " to view or interact with this courseware component."
        ),
        default=False,
        scope=Scope.settings,
    )

    default_time_limit_minutes = Integer(
        display_name=_("Time Limit in Minutes"),
        help=_(
            "The number of minutes available to students for viewing or interacting with this courseware component."
        ),
        default=None,
        scope=Scope.settings,
    )

    is_proctored_enabled = Boolean(
        display_name=_("Is Proctoring Enabled"),
        help=_(
            "This setting indicates whether this exam is a proctored exam."
        ),
        default=False,
        scope=Scope.settings,
    )

    exam_review_rules = String(
        display_name=_("Software Secure Review Rules"),
        help=_(
            "This setting indicates what rules the proctoring team should follow when viewing the videos."
        ),
        default='',
        scope=Scope.settings,
    )

    hide_after_due = Boolean(
        display_name=_("Hide Exam Results After Due Date"),
        help=_(
            "This setting overrides the default behavior of showing exam results after the due date has passed."
            " Currently only supported for timed exams."
        ),
        default=False,
        scope=Scope.settings,
    )

    is_practice_exam = Boolean(
        display_name=_("Is Practice Exam"),
        help=_(
            "This setting indicates whether this exam is for testing purposes only. Practice exams are not verified."
        ),
        default=False,
        scope=Scope.settings,
    )

    @property
    def is_proctored_exam(self):
        """ Alias the is_proctored_enabled field to the more legible is_proctored_exam """
        return self.is_proctored_enabled

    @is_proctored_exam.setter
    def is_proctored_exam(self, value):
        """ Alias the is_proctored_enabled field to the more legible is_proctored_exam """
        self.is_proctored_enabled = value


@XBlock.wants('proctoring')
@XBlock.wants('credit')
@XBlock.needs("user")
@XBlock.needs("bookmarks")
class SequenceModule(SequenceFields, ProctoringFields, XModule):
    """
    Layout module which lays out content in a temporal sequence
    """
    js = {
        'coffee': [resource_string(__name__, 'js/src/sequence/display.coffee')],
        'js': [resource_string(__name__, 'js/src/sequence/display/jquery.sequence.js')],
    }
    css = {
        'scss': [resource_string(__name__, 'css/sequence/display.scss')],
    }
    js_module_name = "Sequence"

    def __init__(self, *args, **kwargs):
        super(SequenceModule, self).__init__(*args, **kwargs)

        # If position is specified in system, then use that instead.
        position = getattr(self.system, 'position', None)
        if position is not None:
            assert isinstance(position, int)
            self.position = self.system.position

    def get_progress(self):
        ''' Return the total progress, adding total done and total available.
        (assumes that each submodule uses the same "units" for progress.)
        '''
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress

    def handle_ajax(self, dispatch, data):  # TODO: bounds checking
        ''' get = request.POST instance '''
        if dispatch == 'goto_position':
            # set position to default value if either 'position' argument not
            # found in request or it is a non-positive integer
            position = data.get('position', u'1')
            if position.isdigit() and int(position) > 0:
                self.position = int(position)
            else:
                self.position = 1
            return json.dumps({'success': True})

        raise NotFoundError('Unexpected dispatch type')

    def student_view(self, context):
        display_items = self.get_display_items()

        # If we're rendering this sequence, but no position is set yet,
        # or exceeds the length of the displayable items,
        # default the position to the first element
        if context.get('requested_child') == 'first':
            self.position = 1
        elif context.get('requested_child') == 'last':
            self.position = len(display_items) or 1
        elif self.position is None or self.position > len(display_items):
            self.position = 1

        ## Returns a set of all types of all sub-children
        contents = []

        fragment = Fragment()
        context = context or {}

        bookmarks_service = self.runtime.service(self, "bookmarks")
        context["username"] = self.runtime.service(self, "user").get_current_user().opt_attrs['edx-platform.username']

        parent_module = self.get_parent()
        display_names = [
            parent_module.display_name_with_default,
            self.display_name_with_default
        ]

        # We do this up here because proctored exam functionality could bypass
        # rendering after this section.
        self._capture_basic_metrics()

        # Is this sequential part of a timed or proctored exam?
        masquerading = context.get('specific_masquerade', False)
        special_exam_html = None
        if self.is_time_limited:
            special_exam_html = self._time_limited_student_view(context)

            # Do we have an applicable alternate rendering
            # from the edx_proctoring subsystem?
            if special_exam_html and not masquerading:
                fragment.add_content(special_exam_html)
                return fragment

        for child in display_items:
            is_bookmarked = bookmarks_service.is_bookmarked(usage_key=child.scope_ids.usage_id)
            context["bookmarked"] = is_bookmarked

            progress = child.get_progress()
            rendered_child = child.render(STUDENT_VIEW, context)
            fragment.add_frag_resources(rendered_child)

            childinfo = {
                'content': rendered_child.content,
                'page_title': getattr(child, 'tooltip_title', ''),
                'progress_status': Progress.to_js_status_str(progress),
                'progress_detail': Progress.to_js_detail_str(progress),
                'type': child.get_icon_class(),
                'id': child.scope_ids.usage_id.to_deprecated_string(),
                'bookmarked': is_bookmarked,
                'path': " > ".join(display_names + [child.display_name_with_default]),
            }

            contents.append(childinfo)

        params = {
            'items': contents,
            'element_id': self.location.html_id(),
            'item_id': self.location.to_deprecated_string(),
            'position': self.position,
            'tag': self.location.category,
            'ajax_url': self.system.ajax_url,
            'next_url': context.get('next_url'),
            'prev_url': context.get('prev_url'),
            'override_hidden_exam': masquerading and special_exam_html is not None,
        }

        fragment.add_content(self.system.render_template("seq_module.html", params))

        self._capture_full_seq_item_metrics(display_items)
        self._capture_current_unit_metrics(display_items)

        # Get all descendant XBlock types and counts
        return fragment

    def _locations_in_subtree(self, node):
        """
        The usage keys for all descendants of an XBlock/XModule as a flat list.

        Includes the location of the node passed in.
        """
        stack = [node]
        locations = []

        while stack:
            curr = stack.pop()
            locations.append(curr.location)
            if curr.has_children:
                stack.extend(curr.get_children())

        return locations

    def _capture_basic_metrics(self):
        """
        Capture basic information about this sequence in New Relic.
        """
        newrelic.agent.add_custom_parameter('seq.block_id', unicode(self.location))
        newrelic.agent.add_custom_parameter('seq.display_name', self.display_name or '')
        newrelic.agent.add_custom_parameter('seq.position', self.position)
        newrelic.agent.add_custom_parameter('seq.is_time_limited', self.is_time_limited)

    def _capture_full_seq_item_metrics(self, display_items):
        """
        Capture information about the number and types of XBlock content in
        the sequence as a whole. We send this information to New Relic so that
        we can do better performance analysis of courseware.
        """
        # Basic count of the number of Units (a.k.a. VerticalBlocks) we have in
        # this learning sequence
        newrelic.agent.add_custom_parameter('seq.num_units', len(display_items))

        # Count of all modules (leaf nodes) in this sequence (e.g. videos,
        # problems, etc.) The units (verticals) themselves are not counted.
        all_item_keys = self._locations_in_subtree(self)
        newrelic.agent.add_custom_parameter('seq.num_items', len(all_item_keys))

        # Count of all modules by block_type (e.g. "video": 2, "discussion": 4)
        block_counts = collections.Counter(usage_key.block_type for usage_key in all_item_keys)
        for block_type, count in block_counts.items():
            newrelic.agent.add_custom_parameter('seq.block_counts.{}'.format(block_type), count)

    def _capture_current_unit_metrics(self, display_items):
        """
        Capture information about the current selected Unit within the Sequence.
        """
        # Positions are stored with indexing starting at 1. If we get into a
        # weird state where the saved position is out of bounds (e.g. the
        # content was changed), avoid going into any details about this unit.
        if 1 <= self.position <= len(display_items):
            # Basic info about the Unit...
            current = display_items[self.position - 1]
            newrelic.agent.add_custom_parameter('seq.current.block_id', unicode(current.location))
            newrelic.agent.add_custom_parameter('seq.current.display_name', current.display_name or '')

            # Examining all items inside the Unit (or split_test, conditional, etc.)
            child_locs = self._locations_in_subtree(current)
            newrelic.agent.add_custom_parameter('seq.current.num_items', len(child_locs))
            curr_block_counts = collections.Counter(usage_key.block_type for usage_key in child_locs)
            for block_type, count in curr_block_counts.items():
                newrelic.agent.add_custom_parameter('seq.current.block_counts.{}'.format(block_type), count)

    def _time_limited_student_view(self, context):
        """
        Delegated rendering of a student view when in a time
        limited view. This ultimately calls down into edx_proctoring
        pip installed djangoapp
        """

        # None = no overridden view rendering
        view_html = None

        proctoring_service = self.runtime.service(self, 'proctoring')
        credit_service = self.runtime.service(self, 'credit')

        # Is this sequence designated as a Timed Examination, which includes
        # Proctored Exams
        feature_enabled = (
            proctoring_service and
            credit_service and
            self.is_time_limited
        )
        if feature_enabled:
            user_id = self.runtime.user_id
            user_role_in_course = 'staff' if self.runtime.user_is_staff else 'student'
            course_id = self.runtime.course_id
            content_id = self.location

            context = {
                'display_name': self.display_name,
                'default_time_limit_mins': (
                    self.default_time_limit_minutes if
                    self.default_time_limit_minutes else 0
                ),
                'is_practice_exam': self.is_practice_exam,
                'due_date': self.due
            }

            # inject the user's credit requirements and fulfillments
            if credit_service:
                credit_state = credit_service.get_credit_state(user_id, course_id)
                if credit_state:
                    context.update({
                        'credit_state': credit_state
                    })

            # See if the edx-proctoring subsystem wants to present
            # a special view to the student rather
            # than the actual sequence content
            #
            # This will return None if there is no
            # overridden view to display given the
            # current state of the user
            view_html = proctoring_service.get_student_view(
                user_id=user_id,
                course_id=course_id,
                content_id=content_id,
                context=context,
                user_role=user_role_in_course
            )

        return view_html

    def get_icon_class(self):
        child_classes = set(child.get_icon_class()
                            for child in self.get_children())
        new_class = 'other'
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class


class SequenceDescriptor(SequenceFields, ProctoringFields, MakoModuleDescriptor, XmlDescriptor):
    """
    A Sequences Descriptor object
    """
    mako_template = 'widgets/sequence-edit.html'
    module_class = SequenceModule
    resources_dir = None

    show_in_read_only_mode = True

    js = {
        'coffee': [resource_string(__name__, 'js/src/sequence/edit.coffee')],
    }
    js_module_name = "SequenceDescriptor"

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                child_block = system.process_xml(etree.tostring(child, encoding='unicode'))
                children.append(child_block.scope_ids.usage_id)
            except Exception as e:
                log.exception("Unable to load child when parsing Sequence. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker(u"ERROR: {0}".format(e))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('sequential')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    @property
    def non_editable_metadata_fields(self):
        """
        `is_entrance_exam` should not be editable in the Studio settings editor.
        """
        non_editable_fields = super(SequenceDescriptor, self).non_editable_metadata_fields
        non_editable_fields.append(self.fields['is_entrance_exam'])
        return non_editable_fields

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing.
        """
        # return key/value fields in a Python dict object
        # values may be numeric / string or dict
        # default implementation is an empty dict
        xblock_body = super(SequenceDescriptor, self).index_dictionary()
        html_body = {
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(html_body)
        else:
            xblock_body["content"] = html_body
        xblock_body["content_type"] = "Sequence"

        return xblock_body
