from fs.errors import ResourceNotFoundError
import logging
from lxml import etree
import requests
import time
import hashlib

from .util.decorators import lazyproperty
from .graders import load_grading_policy
from .modulestore import Location
from .seq_module import SequenceDescriptor, SequenceModule
from .timeparse import parse_time, stringify_time
from .structure_module import StructureModule
from .xmodule import Plugin

log = logging.getLogger(__name__)


def load_policies(policy_list):
    """
    policy_list is a list of dictionaries, each with the following keys:

    class: The name of a registered policy plugin
    condition: An optional dictionary contaning the optional keys:
        ids: A list of user ids for whom this policy should be applied
        roles: A list of user roles for whom this policy should be applied
    args: An option dictionary containing named arguments to pass to the policy plugin
    """
    return [
        Policy.load_class(policy['class'])(condition=policy.get('condition'), **policy.get('params', {}))
        for policy in policy_list
    ]


class CourseModule(StructureModule):

    @property
    def policies(self):
        return load_policies(self.content.get('policy_list', []))

    def apply_policies(self, user):
        # N.B. this code needs to be expanded to handle policies that are
        # time specific and thus return an expire header
        policies_to_apply = [
            policy
            for policy in self.policies
            if policy.applies_to(user)
        ]

        cache_key = self.cache_id(policies_to_apply)

        cached_tree = self.runtime.cache('policy').get(cache_key)

        if cached_tree is not None:
            return cached_tree

        tree = self.usage_tree

        for policy in policies_to_apply:
            tree = policy.apply(tree)

        self.runtime.cache('policy').set(cache_key, tree)
        return tree

    def cache_id(self, policies):
        hasher = hashlib.md5(str(self.usage_tree.as_json()))
        for policy in policies:
            hasher.update(policy.id)
        return hasher.hexdigest()


class Policy(Plugin):
    entry_point = 'policy.v1'

    def __init__(self, condition):
        self.condition = condition
        self.id =  str(id(self))

    def apply(self, tree):
        return tree

    def applies_to(self, user):
        if self.condition is None:
            return True

        # N.B. This code may need to expand to allow a more expressive
        # conditional language
        applies_by_id = user.id in self.condition.get('ids', [])
        applies_by_role = bool(set(user.groups) & set(self.condition.get('roles', set())))

        return applies_by_id or applies_by_role


class CascadeKeys(Policy):
    """
    Policy that cascades the values specified for a set of policy keys
    down the tree, prioritizing policies already set on descendents
    over those being cascaded
    """
    def __init__(self, keys, *args, **kwargs):
        super(CascadeKeys, self).__init__(*args, **kwargs)

        self.keys = keys

    def apply(self, tree):
        def cascade(settings):
            new_settings = dict(settings)
            for key in self.keys:
                if key not in new_settings and key in tree.settings:
                    new_settings[key] = tree.settings[key]
            return new_settings

        children = [
            self.apply(child._replace(settings=cascade(child.settings)))
            for child in tree.children
        ]

        return tree._replace(children=children)

class Reschedule(Policy):
    """
    This policy adds a specified timedelta to all start_dates
    """

    def __init__(self, delta, *args, **kwargs):
        super(CascadeKeys, self).__init__(*args, **kwargs)

        self.delta = delta

    def apply(self, tree):
        children = [
            self.apply(child) for child in tree.children
        ]

        settings = dict(tree.settings)
        if 'start_date' in policy:
            settings['start_date'] = settings['start_date'] + delta

        return tree._replace(settings=settings, children=children)

# class AppendModule(QueryPolicy):
#     """
#     This module will append a policy after each module matching the query.
#     Any keys in policy_to_copy will be copied from the usage node that
#     matches the query.
#     """

#     def __init__(self, query, source, policy_to_copy=None, *args, **kwargs):
#         super(AppendModule, self).__init__(query, *args, **kwargs)
#         self.policy_to_copy = policy_to_copy if policy_to_copy is not None else []
#         self.source = source

#     def update(usage):
#         """
#         Return a list of usages to replace the returned usage with
#         """
#         to_insert = Usage.create_usage(self.source)
#         policy = dict(to_insert.policy)
#         for key in self.policy_to_copy:
#             if key in usage:
#                 policy[key] = usage[key]

#         return [usage, to_insert._replace(policy=policy)] 





class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    class Textbook:
        def __init__(self, title, book_url):
            self.title = title
            self.book_url = book_url
            self.table_of_contents = self._get_toc_from_s3()
            self.start_page = int(self.table_of_contents[0].attrib['page'])

            # The last page should be the last element in the table of contents,
            # but it may be nested. So recurse all the way down the last element
            last_el = self.table_of_contents[-1]
            while last_el.getchildren():
                last_el = last_el[-1]

            self.end_page = int(last_el.attrib['page'])

        @property
        def table_of_contents(self):
            return self.table_of_contents

        def _get_toc_from_s3(self):
            """
            Accesses the textbook's table of contents (default name "toc.xml") at the URL self.book_url

            Returns XML tree representation of the table of contents
            """
            toc_url = self.book_url + 'toc.xml'

            # Get the table of contents from S3
            log.info("Retrieving textbook table of contents from %s" % toc_url)
            try:
                r = requests.get(toc_url)
            except Exception as err:
                msg = 'Error %s: Unable to retrieve textbook table of contents at %s' % (err, toc_url)
                log.error(msg)
                raise Exception(msg)

            # TOC is XML. Parse it
            try:
                table_of_contents = etree.fromstring(r.text)
            except Exception as err:
                msg = 'Error %s: Unable to parse XML for textbook table of contents at %s' % (err, toc_url)
                log.error(msg)
                raise Exception(msg)

            return table_of_contents

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)

        self.textbooks = []
        for title, book_url in self.definition['data']['textbooks']:
            try:
                self.textbooks.append(self.Textbook(title, book_url))
            except:
                # If we can't get to S3 (e.g. on a train with no internet), don't break
                # the rest of the courseware.
                log.exception("Couldn't load textbook ({0}, {1})".format(title, book_url))
                continue

        self.wiki_slug = self.definition['data']['wiki_slug'] or self.location.course

        msg = None
        if self.start is None:
            msg = "Course loaded without a valid start date. id = %s" % self.id
            # hack it -- start in 1970
            self.metadata['start'] = stringify_time(time.gmtime(0))
            log.critical(msg)
            system.error_tracker(msg)

        self.enrollment_start = self._try_parse_time("enrollment_start")
        self.enrollment_end = self._try_parse_time("enrollment_end")
        self.end = self._try_parse_time("end")

        # NOTE: relies on the modulestore to call set_grading_policy() right after
        # init.  (Modulestore is in charge of figuring out where to load the policy from)

        # NOTE (THK): This is a last-minute addition for Fall 2012 launch to dynamically
        #   disable the syllabus content for courses that do not provide a syllabus
        self.syllabus_present = self.system.resources_fs.exists(path('syllabus'))

    def set_grading_policy(self, policy_str):
        """Parse the policy specified in policy_str, and save it"""
        try:
            self._grading_policy = load_grading_policy(policy_str)
        except:
            self.system.error_tracker("Failed to load grading policy")
            # Setting this to an empty dictionary will lead to errors when
            # grading needs to happen, but should allow course staff to see
            # the error log.
            self._grading_policy = {}

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        textbooks = []
        for textbook in xml_object.findall("textbook"):
            textbooks.append((textbook.get('title'), textbook.get('book_url')))
            xml_object.remove(textbook)

        #Load the wiki tag if it exists
        wiki_slug = None
        wiki_tag = xml_object.find("wiki")
        if wiki_tag is not None:
            wiki_slug = wiki_tag.attrib.get("slug", default=None)
            xml_object.remove(wiki_tag)

        definition = super(CourseDescriptor, cls).definition_from_xml(xml_object, system)

        definition.setdefault('data', {})['textbooks'] = textbooks
        definition['data']['wiki_slug'] = wiki_slug

        return definition

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        if self.end_date is None:
            return False

        return time.gmtime() > self.end

    def has_started(self):
        return time.gmtime() > self.start

    @property
    def grader(self):
        return self._grading_policy['GRADER']

    @property
    def grade_cutoffs(self):
        return self._grading_policy['GRADE_CUTOFFS']

    @property
    def tabs(self):
        """
        Return the tabs config, as a python object, or None if not specified.
        """
        return self.metadata.get('tabs')

    @property
    def show_calculator(self):
        return self.metadata.get("show_calculator", None) == "Yes"

    @lazyproperty
    def grading_context(self):
        """
        This returns a dictionary with keys necessary for quickly grading
        a student. They are used by grades.grade()

        The grading context has two keys:
        graded_sections - This contains the sections that are graded, as
            well as all possible children modules that can affect the
            grading. This allows some sections to be skipped if the student
            hasn't seen any part of it.

            The format is a dictionary keyed by section-type. The values are
            arrays of dictionaries containing
                "section_descriptor" : The section descriptor
                "xmoduledescriptors" : An array of xmoduledescriptors that
                    could possibly be in the section, for any student

        all_descriptors - This contains a list of all xmodules that can
            effect grading a student. This is used to efficiently fetch
            all the xmodule state for a StudentModuleCache without walking
            the descriptor tree again.


        """

        all_descriptors = []
        graded_sections = {}

        def yield_descriptor_descendents(module_descriptor):
            for child in module_descriptor.get_children():
                yield child
                for module_descriptor in yield_descriptor_descendents(child):
                    yield module_descriptor

        for c in self.get_children():
            sections = []
            for s in c.get_children():
                if s.metadata.get('graded', False):
                    xmoduledescriptors = list(yield_descriptor_descendents(s))
                    xmoduledescriptors.append(s)

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = { 'section_descriptor' : s, 'xmoduledescriptors' : filter(lambda child: child.has_score, xmoduledescriptors) }

                    section_format = s.metadata.get('format', "")
                    graded_sections[ section_format ] = graded_sections.get( section_format, [] ) + [section_description]

                    all_descriptors.extend(xmoduledescriptors)
                    all_descriptors.append(s)

        return { 'graded_sections' : graded_sections,
                 'all_descriptors' : all_descriptors,}


    @staticmethod
    def make_id(org, course, url_name):
        return '/'.join([org, course, url_name])

    @staticmethod
    def id_to_location(course_id):
        '''Convert the given course_id (org/course/name) to a location object.
        Throws ValueError if course_id is of the wrong format.
        '''
        org, course, name = course_id.split('/')
        return Location('i4x', org, course, 'course', name)

    @staticmethod
    def location_to_id(location):
        '''Convert a location of a course to a course_id.  If location category
        is not "course", raise a ValueError.

        location: something that can be passed to Location
        '''
        loc = Location(location)
        if loc.category != "course":
            raise ValueError("{0} is not a course location".format(loc))
        return "/".join([loc.org, loc.course, loc.name])


    @property
    def id(self):
        """Return the course_id for this course"""
        return self.location_to_id(self.location)

    @property
    def start_date_text(self):
        displayed_start = self._try_parse_time('advertised_start') or self.start
        return time.strftime("%b %d, %Y", displayed_start)

    # An extra property is used rather than the wiki_slug/number because
    # there are courses that change the number for different runs. This allows
    # courses to share the same css_class across runs even if they have
    # different numbers.
    #
    # TODO get rid of this as soon as possible or potentially build in a robust
    # way to add in course-specific styling. There needs to be a discussion
    # about the right way to do this, but arjun will address this ASAP. Also
    # note that the courseware template needs to change when this is removed.
    @property
    def css_class(self):
        return self.metadata.get('css_class', '')

    @property
    def info_sidebar_name(self):
        return self.metadata.get('info_sidebar_name', 'Course Handouts')

    @property
    def discussion_link(self):
        """TODO: This is a quick kludge to allow CS50 (and other courses) to
        specify their own discussion forums as external links by specifying a
        "discussion_link" in their policy JSON file. This should later get
        folded in with Syllabus, Course Info, and additional Custom tabs in a
        more sensible framework later."""
        return self.metadata.get('discussion_link', None)

    @property
    def forum_posts_allowed(self):
        try:
            blackout_periods = [(parse_time(start), parse_time(end))
                                for start, end
                                in self.metadata.get('discussion_blackouts', [])]
            now = time.gmtime()
            for start, end in blackout_periods:
                if start <= now <= end:
                    return False
        except:
            log.exception("Error parsing discussion_blackouts for course {0}".format(self.id))
        
        return True

    @property
    def hide_progress_tab(self):
        """TODO: same as above, intended to let internal CS50 hide the progress tab
        until we get grade integration set up."""
        # Explicit comparison to True because we always want to return a bool.
        return self.metadata.get('hide_progress_tab') == True

    @property
    def title(self):
        return self.display_name

    @property
    def number(self):
        return self.location.course

    @property
    def org(self):
        return self.location.org

