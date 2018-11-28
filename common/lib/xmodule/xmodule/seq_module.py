"""
xModule implementation of a learning sequence
"""

# pylint: disable=abstract-method
import collections
import json
import logging
from datetime import datetime

from lxml import etree
from opaque_keys.edx.keys import UsageKey
from pkg_resources import resource_string
from pytz import UTC
from six import text_type
from web_fragments.fragment import Fragment
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import Boolean, Integer, List, Scope, String

from .exceptions import NotFoundError
from .fields import Date
from .mako_module import MakoModuleDescriptor
from .progress import Progress
from .x_module import STUDENT_VIEW, XModule
from .xml_module import XmlDescriptor

log = logging.getLogger(__name__)

try:
    import newrelic.agent
except ImportError:
    newrelic = None  # pylint: disable=invalid-name

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class SequenceFields(object):
    has_children = True
    completion_mode = XBlockCompletionMode.AGGREGATOR

    # NOTE: Position is 1-indexed.  This is silly, but there are now student
    # positions saved on prod, so it's not easy to fix.
    position = Integer(help="Last tab viewed in this sequence", scope=Scope.user_state)

    due = Date(
        display_name=_("Due Date"),
        help=_("Enter the date by which problems are due."),
        scope=Scope.settings,
    )

    hide_after_due = Boolean(
        display_name=_("Hide sequence content After Due Date"),
        help=_(
            "If set, the sequence content is hidden for non-staff users after the due date has passed."
        ),
        default=False,
        scope=Scope.settings,
    )

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

    is_practice_exam = Boolean(
        display_name=_("Is Practice Exam"),
        help=_(
            "This setting indicates whether this exam is for testing purposes only. Practice exams are not verified."
        ),
        default=False,
        scope=Scope.settings,
    )

    def _get_course(self):
        """
        Return course by course id.
        """
        return self.descriptor.runtime.modulestore.get_course(self.course_id)  # pylint: disable=no-member

    @property
    def is_timed_exam(self):
        """
        Alias the permutation of above fields that corresponds to un-proctored timed exams
        to the more clearly-named is_timed_exam
        """
        return not self.is_proctored_enabled and not self.is_practice_exam and self.is_time_limited

    @property
    def is_proctored_exam(self):
        """ Alias the is_proctored_enabled field to the more legible is_proctored_exam """
        return self.is_proctored_enabled

    @property
    def allow_proctoring_opt_out(self):
        """
        Returns true if the learner should be given the option to choose between
        taking a proctored exam, or opting out to take the exam without proctoring.
        """
        return self._get_course().allow_proctoring_opt_out

    @is_proctored_exam.setter
    def is_proctored_exam(self, value):
        """ Alias the is_proctored_enabled field to the more legible is_proctored_exam """
        self.is_proctored_enabled = value


@XBlock.wants('proctoring')
@XBlock.wants('verification')
@XBlock.wants('gating')
@XBlock.wants('credit')
@XBlock.wants('completion')
@XBlock.needs('user')
@XBlock.needs('bookmarks')
class SequenceModule(SequenceFields, ProctoringFields, XModule):
    """
    Layout module which lays out content in a temporal sequence
    """
    js = {
        'js': [resource_string(__name__, 'js/src/sequence/display.js')],
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

        if dispatch == 'get_completion':
            completion_service = self.runtime.service(self, 'completion')

            usage_key = data.get('usage_key', None)
            if not usage_key:
                return None
            item = self.get_child(UsageKey.from_string(usage_key))
            if not item:
                return None

            complete = completion_service.vertical_is_complete(item)
            return json.dumps({
                'complete': complete
            })
        raise NotFoundError('Unexpected dispatch type')

    @classmethod
    def verify_current_content_visibility(cls, date, hide_after_date):
        """
        Returns whether the content visibility policy passes
        for the given date and hide_after_date values and
        the current date-time.
        """
        return (
            not date or
            not hide_after_date or
            datetime.now(UTC) < date
        )

    def student_view(self, context):
        context = context or {}
        self._capture_basic_metrics()
        banner_text = None
        prereq_met = True
        prereq_meta_info = {}

        if self._required_prereq():
            if self.runtime.user_is_staff:
                banner_text = _('This subsection is unlocked for learners when they meet the prerequisite requirements.')
            else:
                # check if prerequisite has been met
                prereq_met, prereq_meta_info = self._compute_is_prereq_met(True)
        if prereq_met:
            special_html_view = self._hidden_content_student_view(context) or self._special_exam_student_view()
            if special_html_view:
                masquerading_as_specific_student = context.get('specific_masquerade', False)
                banner_text, special_html = special_html_view
                if special_html and not masquerading_as_specific_student:
                    return Fragment(special_html)
        return self._student_view(context, prereq_met, prereq_meta_info, banner_text)

    def _special_exam_student_view(self):
        """
        Checks whether this sequential is a special exam.  If so, returns
        a banner_text or the fragment to display depending on whether
        staff is masquerading.
        """
        if self.is_time_limited:
            special_exam_html = self._time_limited_student_view()
            if special_exam_html:
                banner_text = _("This exam is hidden from the learner.")
                return banner_text, special_exam_html

    def _hidden_content_student_view(self, context):
        """
        Checks whether the content of this sequential is hidden from the
        runtime user. If so, returns a banner_text or the fragment to
        display depending on whether staff is masquerading.
        """
        course = self._get_course()
        if not self._can_user_view_content(course):
            if course.self_paced:
                banner_text = _("Because the course has ended, this assignment is hidden from the learner.")
            else:
                banner_text = _("Because the due date has passed, this assignment is hidden from the learner.")

            hidden_content_html = self.system.render_template(
                'hidden_content.html',
                {
                    'self_paced': course.self_paced,
                    'progress_url': context.get('progress_url'),
                }
            )

            return banner_text, hidden_content_html

    def _can_user_view_content(self, course):
        """
        Returns whether the runtime user can view the content
        of this sequential.
        """
        hidden_date = course.end if course.self_paced else self.due
        return (
            self.runtime.user_is_staff or
            self.verify_current_content_visibility(hidden_date, self.hide_after_due)
        )

    def is_user_authenticated(self, context):
        # NOTE (CCB): We default to true to maintain the behavior in place prior to allowing anonymous access access.
        return context.get('user_authenticated', True)

    def _student_view(self, context, prereq_met, prereq_meta_info, banner_text=None):
        """
        Returns the rendered student view of the content of this
        sequential.  If banner_text is given, it is added to the
        content.
        """
        display_items = self.get_display_items()
        self._update_position(context, len(display_items))

        if prereq_met and not self._is_gate_fulfilled():
            banner_text = _('This section is a prerequisite. You must complete this section in order to unlock additional content.')

        fragment = Fragment()
        params = {
            'items': self._render_student_view_for_items(context, display_items, fragment) if prereq_met else [],
            'element_id': self.location.html_id(),
            'item_id': text_type(self.location),
            'position': self.position,
            'tag': self.location.block_type,
            'ajax_url': self.system.ajax_url,
            'next_url': context.get('next_url'),
            'prev_url': context.get('prev_url'),
            'banner_text': banner_text,
            'save_position': self.is_user_authenticated(context),
            'show_completion': self.is_user_authenticated(context),
            'gated_content': self._get_gated_content_info(prereq_met, prereq_meta_info)
        }
        fragment.add_content(self.system.render_template("seq_module.html", params))

        self._capture_full_seq_item_metrics(display_items)
        self._capture_current_unit_metrics(display_items)

        return fragment

    def _get_gated_content_info(self, prereq_met, prereq_meta_info):
        """
        Returns a dict of information about gated_content context
        """
        gated_content = {}
        gated_content['gated'] = not prereq_met
        gated_content['prereq_url'] = prereq_meta_info['url'] if not prereq_met else None
        gated_content['prereq_section_name'] = prereq_meta_info['display_name'] if not prereq_met else None
        gated_content['gated_section_name'] = self.display_name

        return gated_content

    def _is_gate_fulfilled(self):
        """
        Determines if this section is a prereq and has any unfulfilled milestones.

        Returns:
            True if section has no unfufilled milestones or is not a prerequisite.
            False otherwise
        """
        gating_service = self.runtime.service(self, 'gating')
        if gating_service:
            fulfilled = gating_service.is_gate_fulfilled(
                self.course_id, self.location, self.runtime.user_id
            )
            return fulfilled

        return True

    def _required_prereq(self):
        """
        Checks whether a prerequisite is required for this Section

        Returns:
            milestone if a prereq is required, None otherwise
        """
        gating_service = self.runtime.service(self, 'gating')
        if gating_service:
            milestone = gating_service.required_prereq(
                self.course_id, self.location, 'requires'
            )
            return milestone

        return None

    def _compute_is_prereq_met(self, recalc_on_unmet):
        """
        Evaluate if the user has completed the prerequisite

        Arguments:
            recalc_on_unmet: Recalculate the subsection grade if prereq has not yet been met

        Returns:
            tuple: True|False,
            prereq_meta_info = { 'url': prereq_url, 'display_name': prereq_name}
        """
        gating_service = self.runtime.service(self, 'gating')
        if gating_service:
            return gating_service.compute_is_prereq_met(self.location, self.runtime.user_id, recalc_on_unmet)

        return True, {}

    def _update_position(self, context, number_of_display_items):
        """
        Update the user's sequential position given the context and the
        number_of_display_items
        """

        position = context.get('position')
        if position:
            self.position = position

        # If we're rendering this sequence, but no position is set yet,
        # or exceeds the length of the displayable items,
        # default the position to the first element
        if context.get('requested_child') == 'first':
            self.position = 1
        elif context.get('requested_child') == 'last':
            self.position = number_of_display_items or 1
        elif self.position is None or self.position > number_of_display_items:
            self.position = 1

    def _render_student_view_for_items(self, context, display_items, fragment):
        """
        Updates the given fragment with rendered student views of the given
        display_items.  Returns a list of dict objects with information about
        the given display_items.
        """
        is_user_authenticated = self.is_user_authenticated(context)
        bookmarks_service = self.runtime.service(self, 'bookmarks')
        completion_service = self.runtime.service(self, 'completion')
        context['username'] = self.runtime.service(self, 'user').get_current_user().opt_attrs.get(
            'edx-platform.username')
        display_names = [
            self.get_parent().display_name_with_default,
            self.display_name_with_default
        ]
        contents = []
        for item in display_items:
            # NOTE (CCB): This seems like a hack, but I don't see a better method of determining the type/category.
            item_type = item.get_icon_class()
            usage_id = item.scope_ids.usage_id

            if item_type == 'problem' and not is_user_authenticated:
                log.info(
                    'Problem [%s] was not rendered because anonymous access is not allowed for graded content',
                    usage_id
                )
                continue

            show_bookmark_button = False
            is_bookmarked = False

            if is_user_authenticated:
                show_bookmark_button = True
                is_bookmarked = bookmarks_service.is_bookmarked(usage_key=usage_id)

            context['show_bookmark_button'] = show_bookmark_button
            context['bookmarked'] = is_bookmarked

            rendered_item = item.render(STUDENT_VIEW, context)
            fragment.add_fragment_resources(rendered_item)

            iteminfo = {
                'content': rendered_item.content,
                'page_title': getattr(item, 'tooltip_title', ''),
                'type': item_type,
                'id': text_type(usage_id),
                'bookmarked': is_bookmarked,
                'path': " > ".join(display_names + [item.display_name_with_default]),
                'graded': item.graded
            }

            if is_user_authenticated:
                if item.location.block_type == 'vertical':
                    iteminfo['complete'] = completion_service.vertical_is_complete(item)

            contents.append(iteminfo)

        return contents

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
        if not newrelic:
            return
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
        if not newrelic:
            return
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
        if not newrelic:
            return
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

    def _time_limited_student_view(self):
        """
        Delegated rendering of a student view when in a time
        limited view. This ultimately calls down into edx_proctoring
        pip installed djangoapp
        """

        # None = no overridden view rendering
        view_html = None

        proctoring_service = self.runtime.service(self, 'proctoring')
        credit_service = self.runtime.service(self, 'credit')
        verification_service = self.runtime.service(self, 'verification')

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
                'allow_proctoring_opt_out': self.allow_proctoring_opt_out,
                'due_date': self.due
            }

            # inject the user's credit requirements and fulfillments
            if credit_service:
                credit_state = credit_service.get_credit_state(user_id, course_id)
                if credit_state:
                    context.update({
                        'credit_state': credit_state
                    })

            # inject verification status
            if verification_service:
                verification_status = verification_service.get_status(user_id)
                context.update({
                    'verification_status': verification_status['status'],
                    'reverify_url': verification_service.reverify_url(),
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
    A Sequence's Descriptor object
    """
    mako_template = 'widgets/sequence-edit.html'
    module_class = SequenceModule
    resources_dir = None

    show_in_read_only_mode = True

    js = {
        'js': [resource_string(__name__, 'js/src/sequence/edit.js')],
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


class HighlightsFields(object):
    """Only Sections have summaries now, but we may expand that later."""
    highlights = List(
        help=_("A list summarizing what students should look forward to in this section."),
        scope=Scope.settings
    )


class SectionModule(HighlightsFields, SequenceModule):
    """Module for a Section/Chapter."""


class SectionDescriptor(HighlightsFields, SequenceDescriptor):
    """Descriptor for a Section/Chapter."""
    module_class = SectionModule
