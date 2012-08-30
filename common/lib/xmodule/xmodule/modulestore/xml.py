import hashlib
import json
import logging
import os
import re

from collections import defaultdict
from cStringIO import StringIO
from fs.osfs import OSFS
from importlib import import_module
from lxml import etree
from lxml.html import HtmlComment
from path import path

from xmodule.errortracker import ErrorLog, make_error_tracker
from xmodule.course_module import CourseDescriptor
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XModuleDescriptor, XMLParsingSystem

from . import ModuleStoreBase, Location
from .exceptions import ItemNotFoundError

edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True)

etree.set_default_parser(edx_xml_parser)

log = logging.getLogger('mitx.' + __name__)

# VS[compat]
# TODO (cpennington): Remove this once all fall 2012 courses have been imported
# into the cms from xml
def clean_out_mako_templating(xml_string):
    xml_string = xml_string.replace('%include', 'include')
    xml_string = re.sub("(?m)^\s*%.*$", '', xml_string)
    return xml_string

class ImportSystem(XMLParsingSystem, MakoDescriptorSystem):
    def __init__(self, xmlstore, course_id, course_dir,
                 policy, error_tracker, **kwargs):
        """
        A class that handles loading from xml.  Does some munging to ensure that
        all elements have unique slugs.

        xmlstore: the XMLModuleStore to store the loaded modules in
        """
        self.unnamed = defaultdict(int)     # category -> num of new url_names for that category
        self.used_names = defaultdict(set)  # category -> set of used url_names
        self.org, self.course, self.url_name = course_id.split('/')

        def process_xml(xml):
            """Takes an xml string, and returns a XModuleDescriptor created from
            that xml.
            """

            def make_name_unique(xml_data):
                """
                Make sure that the url_name of xml_data is unique.  If a previously loaded
                unnamed descriptor stole this element's url_name, create a new one.

                Removes 'slug' attribute if present, and adds or overwrites the 'url_name' attribute.
                """
                # VS[compat]. Take this out once course conversion is done (perhaps leave the uniqueness check)

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

                def fallback_name():
                    """Return the fallback name for this module.  This is a function instead of a variable
                    because we want it to be lazy."""
                    # use the hash of the content--the first 12 bytes should be plenty.
                    return tag + "_" + hashlib.sha1(xml).hexdigest()[:12]

                # Fallback if there was nothing we could use:
                if url_name is None or url_name == "":
                    url_name = fallback_name()
                    # Don't log a warning--we don't need this in the log.  Do
                    # put it in the error tracker--content folks need to see it.
                    need_uniq_names = ('problem', 'sequence', 'video', 'course', 'chapter')

                    if tag in need_uniq_names:
                        error_tracker("ERROR: no name of any kind specified for {tag}.  Student "
                                      "state won't work right.  Problem xml: '{xml}...'".format(tag=tag, xml=xml[:100]))
                    else:
                        # TODO (vshnayder): We may want to enable this once course repos are cleaned up.
                        # (or we may want to give up on the requirement for non-state-relevant issues...)
                        #error_tracker("WARNING: no name specified for module. xml='{0}...'".format(xml[:100]))
                        pass

                # Make sure everything is unique
                if url_name in self.used_names[tag]:
                    msg = ("Non-unique url_name in xml.  This may break content.  url_name={0}.  Content={1}"
                                .format(url_name, xml[:100]))
                    error_tracker("ERROR: " + msg)
                    log.warning(msg)
                    # Just set name to fallback_name--if there are multiple things with the same fallback name,
                    # they are actually identical, so it's fragile, but not immediately broken.
                    url_name = fallback_name()

                self.used_names[tag].add(url_name)
                xml_data.set('url_name', url_name)

            try:
                # VS[compat]
                # TODO (cpennington): Remove this once all fall 2012 courses
                # have been imported into the cms from xml
                xml = clean_out_mako_templating(xml)
                xml_data = etree.fromstring(xml)
            except Exception as err:
                log.warning("Unable to parse xml: {err}, xml: {xml}".format(
                    err=str(err), xml=xml))
                raise

            make_name_unique(xml_data)

            descriptor = XModuleDescriptor.load_from_xml(
                etree.tostring(xml_data), self, self.org,
                self.course, xmlstore.default_class)
            descriptor.metadata['data_dir'] = course_dir

            xmlstore.modules[course_id][descriptor.location] = descriptor

            if xmlstore.eager:
                descriptor.get_children()
            return descriptor

        render_template = lambda: ''
        # TODO (vshnayder): we are somewhat architecturally confused in the loading code:
        # load_item should actually be get_instance, because it expects the course-specific
        # policy to be loaded.  For now, just add the course_id here...
        load_item = lambda location: xmlstore.get_instance(course_id, location)
        resources_fs = OSFS(xmlstore.data_dir / course_dir)

        MakoDescriptorSystem.__init__(self, load_item, resources_fs,
                                      error_tracker, render_template, **kwargs)
        XMLParsingSystem.__init__(self, load_item, resources_fs,
                                  error_tracker, process_xml, policy, **kwargs)


class XMLModuleStore(ModuleStoreBase):
    """
    An XML backed ModuleStore
    """
    def __init__(self, data_dir, default_class=None, eager=False,
                 course_dirs=None):
        """
        Initialize an XMLModuleStore from data_dir

        data_dir: path to data directory containing the course directories

        default_class: dot-separated string defining the default descriptor
            class to use if none is specified in entry_points

        eager: If true, load the modules children immediately to force the
            entire course tree to be parsed

        course_dirs: If specified, the list of course_dirs to load. Otherwise,
            load all course dirs
        """
        ModuleStoreBase.__init__(self)

        self.eager = eager
        self.data_dir = path(data_dir)
        self.modules = defaultdict(dict)  # course_id -> dict(location -> XModuleDescriptor)
        self.courses = {}  # course_dir -> XModuleDescriptor for the course
        self.errored_courses = {}  # course_dir -> errorlog, for dirs that failed to load

        if default_class is None:
            self.default_class = None
        else:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_

        # TODO (cpennington): We need a better way of selecting specific sets of
        # debug messages to enable. These were drowning out important messages
        #log.debug('XMLModuleStore: eager=%s, data_dir = %s' % (eager, self.data_dir))
        #log.debug('default_class = %s' % self.default_class)

        # If we are specifically asked for missing courses, that should
        # be an error.  If we are asked for "all" courses, find the ones
        # that have a course.xml
        if course_dirs is None:
            course_dirs = [d for d in os.listdir(self.data_dir) if
                           os.path.exists(self.data_dir / d / "course.xml")]

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
            msg = "Failed to load course '{0}': {1}".format(course_dir, str(e))
            log.exception(msg)
            errorlog.tracker(msg)

        if course_descriptor is not None:
            self.courses[course_dir] = course_descriptor
            self._location_errors[course_descriptor.location] = errorlog
        else:
            # Didn't load course.  Instead, save the errors elsewhere.
            self.errored_courses[course_dir] = errorlog



    def __unicode__(self):
        '''
        String representation - for debugging
        '''
        return '<XMLModuleStore>data_dir=%s, %d courses, %d modules' % (
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
            log.debug("Loading policy from {0}".format(policy_path))
            with open(policy_path) as f:
                return json.load(f)
        except (IOError, ValueError) as err:
            msg = "Error loading course policy from {0}".format(policy_path)
            tracker(msg)
            log.warning(msg + " " + str(err))
        return {}


    def read_grading_policy(self, paths, tracker):
        """Load a grading policy from the specified paths, in order, if it exists."""
        # Default to a blank policy
        policy_str = ""

        for policy_path in paths:
            if not os.path.exists(policy_path):
                continue
            log.debug("Loading grading policy from {0}".format(policy_path))
            try:
                with open(policy_path) as grading_policy_file:
                    policy_str = grading_policy_file.read()
                    # if we successfully read the file, stop looking at backups
                    break
            except (IOError):
                msg = "Unable to load course settings file from '{0}'".format(policy_path)
                tracker(msg)
                log.warning(msg)

        return policy_str


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

            course_data = etree.parse(course_file,parser=edx_xml_parser).getroot()

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
                          " Using default '{default}'".format(
                        dir=course_dir,
                        default=course_dir
                        ))
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
            system = ImportSystem(self, course_id, course_dir, policy, tracker)

            course_descriptor = system.process_xml(etree.tostring(course_data))

            # NOTE: The descriptors end up loading somewhat bottom up, which
            # breaks metadata inheritance via get_children().  Instead
            # (actually, in addition to, for now), we do a final inheritance pass
            # after we have the course descriptor.
            XModuleDescriptor.compute_inherited_metadata(course_descriptor)

            # Try to load grading policy
            paths = [self.data_dir / course_dir / 'grading_policy.json']
            if policy_dir:
                paths = [policy_dir / 'grading_policy.json'] + paths

            policy_str = self.read_grading_policy(paths, tracker)
            course_descriptor.set_grading_policy(policy_str)


            log.debug('========> Done with course import from {0}'.format(course_dir))
            return course_descriptor


    def get_instance(self, course_id, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at
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

    def get_item(self, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the most item with the most
        recent revision

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """
        raise NotImplementedError("XMLModuleStores can't guarantee that definitions"
                                  " are unique. Use get_instance.")


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
        return dict( (k, self.errored_courses[k].errors) for k in self.errored_courses)

    def create_item(self, location):
        raise NotImplementedError("XMLModuleStores are read-only")


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
