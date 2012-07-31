import logging
import os
import re

from fs.osfs import OSFS
from importlib import import_module
from lxml import etree
from path import path
from xmodule.errortracker import ErrorLog, make_error_tracker
from xmodule.x_module import XModuleDescriptor, XMLParsingSystem
from xmodule.course_module import CourseDescriptor
from xmodule.mako_module import MakoDescriptorSystem
from cStringIO import StringIO

from . import ModuleStore, Location
from .exceptions import ItemNotFoundError

etree.set_default_parser(
    etree.XMLParser(dtd_validation=False, load_dtd=False,
                    remove_comments=True, remove_blank_text=True))

log = logging.getLogger('mitx.' + __name__)

# VS[compat]
# TODO (cpennington): Remove this once all fall 2012 courses have been imported
# into the cms from xml
def clean_out_mako_templating(xml_string):
    xml_string = xml_string.replace('%include', 'include')
    xml_string = re.sub("(?m)^\s*%.*$", '', xml_string)
    return xml_string

class ImportSystem(XMLParsingSystem, MakoDescriptorSystem):
    def __init__(self, xmlstore, org, course, course_dir, error_tracker, **kwargs):
        """
        A class that handles loading from xml.  Does some munging to ensure that
        all elements have unique slugs.

        xmlstore: the XMLModuleStore to store the loaded modules in
        """
        self.unnamed_modules = 0
        self.used_slugs = set()

        def process_xml(xml):
            try:
                # VS[compat]
                # TODO (cpennington): Remove this once all fall 2012 courses
                # have been imported into the cms from xml
                xml = clean_out_mako_templating(xml)
                xml_data = etree.fromstring(xml)
            except:
                log.exception("Unable to parse xml: {xml}".format(xml=xml))
                raise

            # VS[compat]. Take this out once course conversion is done
            if xml_data.get('slug') is None and xml_data.get('url_name') is None:
                if xml_data.get('name'):
                    slug = Location.clean(xml_data.get('name'))
                elif xml_data.get('display_name'):
                    slug = Location.clean(xml_data.get('display_name'))
                else:
                    self.unnamed_modules += 1
                    slug = '{tag}_{count}'.format(tag=xml_data.tag,
                                                  count=self.unnamed_modules)

                while slug in self.used_slugs:
                    self.unnamed_modules += 1
                    slug = '{slug}_{count}'.format(slug=slug,
                                                   count=self.unnamed_modules)

                self.used_slugs.add(slug)
                # log.debug('-> slug=%s' % slug)
                xml_data.set('url_name', slug)

            descriptor = XModuleDescriptor.load_from_xml(
                etree.tostring(xml_data), self, org,
                course, xmlstore.default_class)

            #log.debug('==> importing descriptor location %s' %
            #          repr(descriptor.location))
            descriptor.metadata['data_dir'] = course_dir

            xmlstore.modules[descriptor.location] = descriptor

            if xmlstore.eager:
                descriptor.get_children()
            return descriptor

        render_template = lambda: ''
        load_item = xmlstore.get_item
        resources_fs = OSFS(xmlstore.data_dir / course_dir)

        MakoDescriptorSystem.__init__(self, load_item, resources_fs,
                                      error_tracker, render_template, **kwargs)
        XMLParsingSystem.__init__(self, load_item, resources_fs,
                                  error_tracker, process_xml, **kwargs)


class XMLModuleStore(ModuleStore):
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

        self.eager = eager
        self.data_dir = path(data_dir)
        self.modules = {}  # location -> XModuleDescriptor
        self.courses = {}  # course_dir -> XModuleDescriptor for the course
        self.location_errors = {}    # location -> ErrorLog


        if default_class is None:
            self.default_class = None
        else:
            module_path, _, class_name = default_class.rpartition('.')
            #log.debug('module_path = %s' % module_path)
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
            try:
                # make a tracker, then stick in the right place once the course loads
                # and we know its location
                errorlog = make_error_tracker()
                course_descriptor = self.load_course(course_dir, errorlog.tracker)
                self.courses[course_dir] = course_descriptor
                self.location_errors[course_descriptor.location] = errorlog
            except:
                msg = "Failed to load course '%s'" % course_dir
                log.exception(msg)


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

            course_data = etree.parse(course_file).getroot()
            org = course_data.get('org')

            if org is None:
                log.error("No 'org' attribute set for course in {dir}. "
                          "Using default 'edx'".format(dir=course_dir))
                org = 'edx'

            course = course_data.get('course')

            if course is None:
                log.error("No 'course' attribute set for course in {dir}."
                          " Using default '{default}'".format(
                        dir=course_dir,
                        default=course_dir
                        ))
                course = course_dir

            system = ImportSystem(self, org, course, course_dir, tracker)

            course_descriptor = system.process_xml(etree.tostring(course_data))
            log.debug('========> Done with course import from {0}'.format(course_dir))
            return course_descriptor


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
        location = Location(location)
        try:
            return self.modules[location]
        except KeyError:
            raise ItemNotFoundError(location)


    def get_item_errors(self, location):
        """
        Return list of errors for this location, if any.  Raise the same
        errors as get_item if location isn't present.

        NOTE: This only actually works for courses in the xml datastore--
        will return an empty list for all other modules.
        """
        location = Location(location)
        # check that item is present
        self.get_item(location)

        # now look up errors
        if location in self.location_errors:
            return self.location_errors[location].errors
        return []

    def get_courses(self, depth=0):
        """
        Returns a list of course descriptors.  If there were errors on loading,
        some of these may be ErrorDescriptors instead.
        """
        return self.courses.values()

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
