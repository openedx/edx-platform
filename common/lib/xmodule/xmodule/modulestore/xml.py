import hashlib
import json
import logging
import os
import re
import sys
import glob

from collections import defaultdict
from cStringIO import StringIO
from fs.osfs import OSFS
from importlib import import_module
from lxml import etree
from path import path

from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import make_error_tracker, exc_info_to_str
from xmodule.course_module import CourseDescriptor
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XMLParsingSystem

from xmodule.html_module import HtmlDescriptor
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.field_data import DictFieldData

from . import ModuleStoreBase, Location, XML_MODULESTORE_TYPE

from .exceptions import ItemNotFoundError
from .inheritance import compute_inherited_metadata

edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True)

etree.set_default_parser(edx_xml_parser)

log = logging.getLogger(__name__)


# VS[compat]
# TODO (cpennington): Remove this once all fall 2012 courses have been imported
# into the cms from xml
def clean_out_mako_templating(xml_string):
    xml_string = xml_string.replace('%include', 'include')
    xml_string = re.sub(r"(?m)^\s*%.*$", '', xml_string)
    return xml_string


class ImportSystem(XMLParsingSystem, MakoDescriptorSystem):
    def __init__(self, xmlstore, course_id, course_dir,
                 error_tracker, parent_tracker,
                 load_error_modules=True, **kwargs):
        """
        A class that handles loading from xml.  Does some munging to ensure that
        all elements have unique slugs.

        xmlstore: the XMLModuleStore to store the loaded modules in
        """
        self.unnamed = defaultdict(int)  # category -> num of new url_names for that category
        self.used_names = defaultdict(set)  # category -> set of used url_names
        self.org, self.course, self.url_name = course_id.split('/')
        # cdodge: adding the course_id as passed in for later reference rather than having to recomine the org/course/url_name
        self.course_id = course_id
        self.load_error_modules = load_error_modules

        def process_xml(xml):
            """Takes an xml string, and returns a XBlock created from
            that xml.
            """

            def make_name_unique(xml_data):
                """
                Make sure that the url_name of xml_data is unique.  If a previously loaded
                unnamed descriptor stole this element's url_name, create a new one.

                Removes 'slug' attribute if present, and adds or overwrites the 'url_name' attribute.
                """
                # VS[compat]. Take this out once course conversion is done (perhaps leave the uniqueness check)

                # tags that really need unique names--they store (or should store) state.
                need_uniq_names = ('problem', 'sequential', 'video', 'course', 'chapter',
                                   'videosequence', 'poll_question', 'timelimit')

                attr = xml_data.attrib
                tag = xml_data.tag
                id = lambda x: x
                # Things to try to get a name, in order  (key, cleaning function, remove key after reading?)
                lookups = [('url_name', id, False),
                           ('slug', id, True),
                           ('name', Location.clean, False),
                           ('display_name', Location.clean, False)]

                url_name = None
                for key, clean, remove in lookups:
                    if key in attr:
                        url_name = clean(attr[key])
                        if remove:
                            del attr[key]
                        break

                def looks_like_fallback(url_name):
                    """Does this look like something that came from fallback_name()?"""
                    return (url_name is not None
                            and url_name.startswith(tag)
                            and re.search('[0-9a-fA-F]{12}$', url_name))

                def fallback_name(orig_name=None):
                    """Return the fallback name for this module.  This is a function instead of a variable
                    because we want it to be lazy."""
                    if looks_like_fallback(orig_name):
                        # We're about to re-hash, in case something changed, so get rid of the tag_ and hash
                        orig_name = orig_name[len(tag) + 1:-12]
                    # append the hash of the content--the first 12 bytes should be plenty.
                    orig_name = "_" + orig_name if orig_name not in (None, "") else ""
                    xml_bytes = xml.encode('utf8')
                    return tag + orig_name + "_" + hashlib.sha1(xml_bytes).hexdigest()[:12]

                # Fallback if there was nothing we could use:
                if url_name is None or url_name == "":
                    url_name = fallback_name()
                    # Don't log a warning--we don't need this in the log.  Do
                    # put it in the error tracker--content folks need to see it.

                    if tag in need_uniq_names:
                        error_tracker("PROBLEM: no name of any kind specified for {tag}.  Student "
                                      "state will not be properly tracked for this module.  Problem xml:"
                                      " '{xml}...'".format(tag=tag, xml=xml[:100]))
                    else:
                        # TODO (vshnayder): We may want to enable this once course repos are cleaned up.
                        # (or we may want to give up on the requirement for non-state-relevant issues...)
                        # error_tracker("WARNING: no name specified for module. xml='{0}...'".format(xml[:100]))
                        pass

                # Make sure everything is unique
                if url_name in self.used_names[tag]:
                    # Always complain about modules that store state.  If it
                    # doesn't store state, don't complain about things that are
                    # hashed.
                    if tag in need_uniq_names:
                        msg = ("Non-unique url_name in xml.  This may break state tracking for content."
                               "  url_name={0}.  Content={1}".format(url_name, xml[:100]))
                        error_tracker("PROBLEM: " + msg)
                        log.warning(msg)
                        # Just set name to fallback_name--if there are multiple things with the same fallback name,
                        # they are actually identical, so it's fragile, but not immediately broken.

                        # TODO (vshnayder): if the tag is a pointer tag, this will
                        # break the content because we won't have the right link.
                        # That's also a legitimate attempt to reuse the same content
                        # from multiple places.  Once we actually allow that, we'll
                        # need to update this to complain about non-unique names for
                        # definitions, but allow multiple uses.
                        url_name = fallback_name(url_name)

                self.used_names[tag].add(url_name)
                xml_data.set('url_name', url_name)

            try:
                # VS[compat]
                # TODO (cpennington): Remove this once all fall 2012 courses
                # have been imported into the cms from xml
                xml = clean_out_mako_templating(xml)
                xml_data = etree.fromstring(xml)

                make_name_unique(xml_data)

                descriptor = create_block_from_xml(
                    etree.tostring(xml_data, encoding='unicode'), self, self.org,
                    self.course, xmlstore.default_class)
            except Exception as err:
                if not self.load_error_modules:
                    raise

                # Didn't load properly.  Fall back on loading as an error
                # descriptor.  This should never error due to formatting.

                msg = "Error loading from xml. " + unicode(err)[:200]
                log.warning(msg)
                # Normally, we don't want lots of exception traces in our logs from common
                # content problems.  But if you're debugging the xml loading code itself,
                # uncomment the next line.
                log.exception(msg)

                self.error_tracker(msg)
                err_msg = msg + "\n" + exc_info_to_str(sys.exc_info())
                descriptor = ErrorDescriptor.from_xml(
                    xml,
                    self,
                    self.org,
                    self.course,
                    err_msg
                )

            descriptor.data_dir = course_dir

            xmlstore.modules[course_id][descriptor.location] = descriptor

            if hasattr(descriptor, 'children'):
                for child in descriptor.get_children():
                    parent_tracker.add_parent(child.location, descriptor.location)

            # After setting up the descriptor, save any changes that we have
            # made to attributes on the descriptor to the underlying KeyValueStore.
            descriptor.save()
            return descriptor

        render_template = lambda: ''
        # TODO (vshnayder): we are somewhat architecturally confused in the loading code:
        # load_item should actually be get_instance, because it expects the course-specific
        # policy to be loaded.  For now, just add the course_id here...
        load_item = lambda location: xmlstore.get_instance(course_id, location)
        resources_fs = OSFS(xmlstore.data_dir / course_dir)
        super(ImportSystem, self).__init__(
            load_item=load_item,
            resources_fs=resources_fs,
            render_template=render_template,
            error_tracker=error_tracker,
            process_xml=process_xml,
            **kwargs
        )


def create_block_from_xml(xml_data, system, org=None, course=None, default_class=None):
    """
    Create an XBlock instance from XML data.

    `xml_data' is a string containing valid xml.

    `system` is an XMLParsingSystem.

    `org` and `course` are optional strings that will be used in the generated
    block's url identifiers.

    `default_class` is the class to instantiate of the XML indicates a class
    that can't be loaded.

    Returns the fully instantiated XBlock.

    """
    node = etree.fromstring(xml_data)
    raw_class = XBlock.load_class(node.tag, default_class)
    xblock_class = system.mixologist.mix(raw_class)

    # leave next line commented out - useful for low-level debugging
    # log.debug('[create_block_from_xml] tag=%s, class=%s' % (node.tag, xblock_class))

    url_name = node.get('url_name', node.get('slug'))
    location = Location('i4x', org, course, node.tag, url_name)

    scope_ids = ScopeIds(None, location.category, location, location)
    xblock = xblock_class.parse_xml(node, system, scope_ids)
    return xblock


class ParentTracker(object):
    """A simple class to factor out the logic for tracking location parent pointers."""
    def __init__(self):
        """
        Init
        """
        # location -> set(parents).  Not using defaultdict because we care about the empty case.
        self._parents = dict()

    def add_parent(self, child, parent):
        """
        Add a parent of child location to the set of parents.  Duplicate calls have no effect.

        child and parent must be something that can be passed to Location.
        """
        child = Location(child)
        parent = Location(parent)
        s = self._parents.setdefault(child, set())
        s.add(parent)

    def is_known(self, child):
        """
        returns True iff child has some parents.
        """
        child = Location(child)
        return child in self._parents

    def make_known(self, location):
        """Tell the parent tracker about an object, without registering any
        parents for it.  Used for the top level course descriptor locations."""
        self._parents.setdefault(location, set())

    def parents(self, child):
        """
        Return a list of the parents of this child.  If not is_known(child), will throw a KeyError
        """
        child = Location(child)
        return list(self._parents[child])


class XMLModuleStore(ModuleStoreBase):
    """
    An XML backed ModuleStore
    """
    def __init__(self, data_dir, default_class=None, course_dirs=None, load_error_modules=True, **kwargs):
        """
        Initialize an XMLModuleStore from data_dir

        data_dir: path to data directory containing the course directories

        default_class: dot-separated string defining the default descriptor
            class to use if none is specified in entry_points

        course_dirs: If specified, the list of course_dirs to load. Otherwise,
            load all course dirs
        """
        super(XMLModuleStore, self).__init__(**kwargs)

        self.data_dir = path(data_dir)
        self.modules = defaultdict(dict)  # course_id -> dict(location -> XBlock)
        self.courses = {}  # course_dir -> XBlock for the course
        self.errored_courses = {}  # course_dir -> errorlog, for dirs that failed to load

        self.load_error_modules = load_error_modules

        if default_class is None:
            self.default_class = None
        else:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_

        self.parent_trackers = defaultdict(ParentTracker)

        # If we are specifically asked for missing courses, that should
        # be an error.  If we are asked for "all" courses, find the ones
        # that have a course.xml. We sort the dirs in alpha order so we always
        # read things in the same order (OS differences in load order have
        # bitten us in the past.)
        if course_dirs is None:
            course_dirs = sorted([d for d in os.listdir(self.data_dir) if
                                  os.path.exists(self.data_dir / d / "course.xml")])
        for course_dir in course_dirs:
            self.try_load_course(course_dir)

    def try_load_course(self, course_dir):
        '''
        Load a course, keeping track of errors as we go along.
        '''
        # Special-case code here, since we don't have a location for the
        # course before it loads.
        # So, make a tracker to track load-time errors, then put in the right
        # place after the course loads and we have its location
        errorlog = make_error_tracker()
        course_descriptor = None
        try:
            course_descriptor = self.load_course(course_dir, errorlog.tracker)
        except Exception as e:
            msg = "ERROR: Failed to load course '{0}': {1}".format(course_dir.encode("utf-8"),
                    unicode(e))
            log.exception(msg)
            errorlog.tracker(msg)

        if course_descriptor is not None and not isinstance(course_descriptor, ErrorDescriptor):
            self.courses[course_dir] = course_descriptor
            self._location_errors[course_descriptor.location] = errorlog
            self.parent_trackers[course_descriptor.id].make_known(course_descriptor.location)
        else:
            # Didn't load course.  Instead, save the errors elsewhere.
            self.errored_courses[course_dir] = errorlog

    def __unicode__(self):
        '''
        String representation - for debugging
        '''
        return '<XMLModuleStore data_dir=%r, %d courses, %d modules>' % (
            self.data_dir, len(self.courses), len(self.modules))

    def load_policy(self, policy_path, tracker):
        """
        Attempt to read a course policy from policy_path.  If the file
        exists, but is invalid, log an error and return {}.

        If the policy loads correctly, returns the deserialized version.
        """
        if not os.path.exists(policy_path):
            return {}
        try:
            with open(policy_path) as f:
                return json.load(f)
        except (IOError, ValueError) as err:
            msg = "ERROR: loading course policy from {0}".format(policy_path)
            tracker(msg)
            log.warning(msg + " " + str(err))
        return {}

    def load_course(self, course_dir, tracker):
        """
        Load a course into this module store
        course_path: Course directory name

        returns a CourseDescriptor for the course
        """
        log.debug('========> Starting course import from {0}'.format(course_dir))

        with open(self.data_dir / course_dir / "course.xml") as course_file:

            # VS[compat]
            # TODO (cpennington): Remove this once all fall 2012 courses have
            # been imported into the cms from xml
            course_file = StringIO(clean_out_mako_templating(course_file.read()))

            course_data = etree.parse(course_file, parser=edx_xml_parser).getroot()

            org = course_data.get('org')

            if org is None:
                msg = ("No 'org' attribute set for course in {dir}. "
                       "Using default 'edx'".format(dir=course_dir))
                log.warning(msg)
                tracker(msg)
                org = 'edx'

            course = course_data.get('course')

            if course is None:
                msg = ("No 'course' attribute set for course in {dir}."
                       " Using default '{default}'".format(dir=course_dir,
                                                           default=course_dir
                                                           )
                       )
                log.warning(msg)
                tracker(msg)
                course = course_dir

            url_name = course_data.get('url_name', course_data.get('slug'))
            policy_dir = None
            if url_name:
                policy_dir = self.data_dir / course_dir / 'policies' / url_name
                policy_path = policy_dir / 'policy.json'

                policy = self.load_policy(policy_path, tracker)

                # VS[compat]: remove once courses use the policy dirs.
                if policy == {}:
                    old_policy_path = self.data_dir / course_dir / 'policies' / '{0}.json'.format(url_name)
                    policy = self.load_policy(old_policy_path, tracker)
            else:
                policy = {}
                # VS[compat] : 'name' is deprecated, but support it for now...
                if course_data.get('name'):
                    url_name = Location.clean(course_data.get('name'))
                    tracker("'name' is deprecated for module xml.  Please use "
                            "display_name and url_name.")
                else:
                    raise ValueError("Can't load a course without a 'url_name' "
                                     "(or 'name') set.  Set url_name.")

            course_id = CourseDescriptor.make_id(org, course, url_name)
            system = ImportSystem(
                xmlstore=self,
                course_id=course_id,
                course_dir=course_dir,
                error_tracker=tracker,
                parent_tracker=self.parent_trackers[course_id],
                load_error_modules=self.load_error_modules,
                policy=policy,
                mixins=self.xblock_mixins,
            )

            course_descriptor = system.process_xml(etree.tostring(course_data, encoding='unicode'))

            # If we fail to load the course, then skip the rest of the loading steps
            if isinstance(course_descriptor, ErrorDescriptor):
                return course_descriptor

            # NOTE: The descriptors end up loading somewhat bottom up, which
            # breaks metadata inheritance via get_children().  Instead
            # (actually, in addition to, for now), we do a final inheritance pass
            # after we have the course descriptor.
            compute_inherited_metadata(course_descriptor)

            # now import all pieces of course_info which is expected to be stored
            # in <content_dir>/info or <content_dir>/info/<url_name>
            self.load_extra_content(system, course_descriptor, 'course_info', self.data_dir / course_dir / 'info', course_dir, url_name)

            # now import all static tabs which are expected to be stored in
            # in <content_dir>/tabs or <content_dir>/tabs/<url_name>
            self.load_extra_content(system, course_descriptor, 'static_tab', self.data_dir / course_dir / 'tabs', course_dir, url_name)

            self.load_extra_content(system, course_descriptor, 'custom_tag_template', self.data_dir / course_dir / 'custom_tags', course_dir, url_name)

            self.load_extra_content(system, course_descriptor, 'about', self.data_dir / course_dir / 'about', course_dir, url_name)

            log.debug('========> Done with course import from {0}'.format(course_dir))
            return course_descriptor

    def load_extra_content(self, system, course_descriptor, category, base_dir, course_dir, url_name):
        self._load_extra_content(system, course_descriptor, category, base_dir, course_dir)

        # then look in a override folder based on the course run
        if os.path.isdir(base_dir / url_name):
            self._load_extra_content(system, course_descriptor, category, base_dir / url_name, course_dir)

    def _load_extra_content(self, system, course_descriptor, category, path, course_dir):

        for filepath in glob.glob(path / '*'):
            if not os.path.isfile(filepath):
                continue

            with open(filepath) as f:
                try:
                    html = f.read().decode('utf-8')
                    # tabs are referenced in policy.json through a 'slug' which is just the filename without the .html suffix
                    slug = os.path.splitext(os.path.basename(filepath))[0]
                    loc = Location('i4x', course_descriptor.location.org, course_descriptor.location.course, category, slug)
                    module = system.construct_xblock_from_class(
                        HtmlDescriptor,
                        # We're loading a descriptor, so student_id is meaningless
                        # We also don't have separate notions of definition and usage ids yet,
                        # so we use the location for both
                        ScopeIds(None, category, loc, loc),
                        DictFieldData({'data': html, 'location': loc, 'category': category}),
                    )
                    # VS[compat]:
                    # Hack because we need to pull in the 'display_name' for static tabs (because we need to edit them)
                    # from the course policy
                    if category == "static_tab":
                        for tab in course_descriptor.tabs or []:
                            if tab.get('url_slug') == slug:
                                module.display_name = tab['name']
                    module.data_dir = course_dir
                    module.save()
                    self.modules[course_descriptor.id][module.location] = module
                except Exception, e:
                    logging.exception("Failed to load %s. Skipping... \
                            Exception: %s", filepath, unicode(e))
                    system.error_tracker("ERROR: " + unicode(e))

    def get_instance(self, course_id, location, depth=0):
        """
        Returns an XBlock instance for the item at
        location, with the policy for course_id.  (In case two xml
        dirs have different content at the same location, return the
        one for this course_id.)

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """
        location = Location(location)
        try:
            return self.modules[course_id][location]
        except KeyError:
            raise ItemNotFoundError(location)

    def has_item(self, course_id, location):
        """
        Returns True if location exists in this ModuleStore.
        """
        location = Location(location)
        return location in self.modules[course_id]

    def get_item(self, location, depth=0):
        """
        Returns an XBlock instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """
        raise NotImplementedError("XMLModuleStores can't guarantee that definitions"
                                  " are unique. Use get_instance.")

    def get_items(self, location, course_id=None, depth=0):
        items = []

        def _add_get_items(self, location, modules):
            for mod_loc, module in modules.iteritems():
                # Locations match if each value in `location` is None or if the value from `location`
                # matches the value from `mod_loc`
                if all(goal is None or goal == value for goal, value in zip(location, mod_loc)):
                    items.append(module)

        if course_id is None:
            for _, modules in self.modules.iteritems():
                _add_get_items(self, location, modules)
        else:
            _add_get_items(self, location, self.modules[course_id])

        return items

    def get_courses(self, depth=0):
        """
        Returns a list of course descriptors.  If there were errors on loading,
        some of these may be ErrorDescriptors instead.
        """
        return self.courses.values()

    def get_errored_courses(self):
        """
        Return a dictionary of course_dir -> [(msg, exception_str)], for each
        course_dir where course loading failed.
        """
        return dict((k, self.errored_courses[k].errors) for k in self.errored_courses)

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def get_parent_locations(self, location, course_id):
        '''Find all locations that are the parents of this location in this
        course.  Needed for path_to_location().

        returns an iterable of things that can be passed to Location.  This may
        be empty if there are no parents.
        '''
        location = Location.ensure_fully_specified(location)
        if not self.parent_trackers[course_id].is_known(location):
            raise ItemNotFoundError("{0} not in {1}".format(location, course_id))

        return self.parent_trackers[course_id].parents(location)

    def get_modulestore_type(self, course_id):
        """
        Returns a type which identifies which modulestore is servicing the given
        course_id. The return can be either "xml" (for XML based courses) or "mongo" for MongoDB backed courses
        """
        return XML_MODULESTORE_TYPE
