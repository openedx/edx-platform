import hashlib
import itertools
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
from contextlib import contextmanager

from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import make_error_tracker, exc_info_to_str
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XMLParsingSystem, policy_key
from xmodule.modulestore.xml_exporter import DEFAULT_CONTENT_FIELDS
from xmodule.modulestore import ModuleStoreEnum, ModuleStoreReadBase
from xmodule.tabs import CourseTabList
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from opaque_keys.edx.locator import CourseLocator

from xblock.field_data import DictFieldData
from xblock.runtime import DictKeyValueStore, IdGenerator


from .exceptions import ItemNotFoundError
from .inheritance import compute_inherited_metadata, inheriting_field_data

from xblock.fields import ScopeIds, Reference, ReferenceList, ReferenceValueDict

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
        id_generator = CourseLocationGenerator(course_id)

        # cdodge: adding the course_id as passed in for later reference rather than having to recomine the org/course/url_name
        self.course_id = course_id
        self.load_error_modules = load_error_modules
        self.modulestore = xmlstore

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
                                   'videosequence', 'poll_question', 'vertical')

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
                        error_tracker(u"PROBLEM: no name of any kind specified for {tag}.  Student "
                                      u"state will not be properly tracked for this module.  Problem xml:"
                                      u" '{xml}...'".format(tag=tag, xml=xml[:100]))
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
                        msg = (u"Non-unique url_name in xml.  This may break state tracking for content."
                               u"  url_name={0}.  Content={1}".format(url_name, xml[:100]))
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
                    etree.tostring(xml_data, encoding='unicode'),
                    self,
                    id_generator,
                )
            except Exception as err:  # pylint: disable=broad-except
                if not self.load_error_modules:
                    raise

                # Didn't load properly.  Fall back on loading as an error
                # descriptor.  This should never error due to formatting.

                msg = "Error loading from xml. %s"
                log.warning(
                    msg,
                    unicode(err)[:200],
                    # Normally, we don't want lots of exception traces in our logs from common
                    # content problems.  But if you're debugging the xml loading code itself,
                    # uncomment the next line.
                    # exc_info=True
                )

                msg = msg % (unicode(err)[:200])

                self.error_tracker(msg)
                err_msg = msg + "\n" + exc_info_to_str(sys.exc_info())
                descriptor = ErrorDescriptor.from_xml(
                    xml,
                    self,
                    id_generator,
                    err_msg
                )

            descriptor.data_dir = course_dir

            xmlstore.modules[course_id][descriptor.scope_ids.usage_id] = descriptor

            if descriptor.has_children:
                for child in descriptor.get_children():
                    parent_tracker.add_parent(child.scope_ids.usage_id, descriptor.scope_ids.usage_id)

            # After setting up the descriptor, save any changes that we have
            # made to attributes on the descriptor to the underlying KeyValueStore.
            descriptor.save()
            return descriptor

        render_template = lambda template, context: u''

        # TODO (vshnayder): we are somewhat architecturally confused in the loading code:
        # load_item should actually be get_instance, because it expects the course-specific
        # policy to be loaded.  For now, just add the course_id here...
        def load_item(usage_key):
            """Return the XBlock for the specified location"""
            return xmlstore.get_item(usage_key)

        resources_fs = OSFS(xmlstore.data_dir / course_dir)

        super(ImportSystem, self).__init__(
            load_item=load_item,
            resources_fs=resources_fs,
            render_template=render_template,
            error_tracker=error_tracker,
            process_xml=process_xml,
            **kwargs
        )

    # id_generator is ignored, because each ImportSystem is already local to
    # a course, and has it's own id_generator already in place
    def add_node_as_child(self, block, node, id_generator):
        child_block = self.process_xml(etree.tostring(node))
        block.children.append(child_block.scope_ids.usage_id)


class CourseLocationGenerator(IdGenerator):
    """
    IdGenerator for Location-based definition ids and usage ids
    based within a course
    """
    def __init__(self, course_id):
        self.course_id = course_id
        self.autogen_ids = itertools.count(0)

    def create_usage(self, def_id):
        return def_id

    def create_definition(self, block_type, slug=None):
        assert block_type is not None
        if slug is None:
            slug = 'autogen_{}_{}'.format(block_type, self.autogen_ids.next())
        return self.course_id.make_usage_key(block_type, slug)


def _make_usage_key(course_key, value):
    """
    Makes value into a UsageKey inside the specified course.
    If value is already a UsageKey, returns that.
    """
    if isinstance(value, UsageKey):
        return value
    return course_key.make_usage_key_from_deprecated_string(value)


def _convert_reference_fields_to_keys(xblock):  # pylint: disable=invalid-name
    """
    Find all fields of type reference and convert the payload into UsageKeys
    """
    course_key = xblock.scope_ids.usage_id.course_key

    for field in xblock.fields.itervalues():
        if field.is_set_on(xblock):
            field_value = getattr(xblock, field.name)
            if isinstance(field, Reference):
                setattr(xblock, field.name, _make_usage_key(course_key, field_value))
            elif isinstance(field, ReferenceList):
                setattr(xblock, field.name, [_make_usage_key(course_key, ele) for ele in field_value])
            elif isinstance(field, ReferenceValueDict):
                for key, subvalue in field_value.iteritems():
                    assert isinstance(subvalue, basestring)
                    field_value[key] = _make_usage_key(course_key, subvalue)
                setattr(xblock, field.name, field_value)


def create_block_from_xml(xml_data, system, id_generator):
    """
    Create an XBlock instance from XML data.

    Args:
        xml_data (string): A string containing valid xml.
        system (XMLParsingSystem): The :class:`.XMLParsingSystem` used to connect the block
            to the outside world.
        id_generator (IdGenerator): An :class:`~xblock.runtime.IdGenerator` that
            will be used to construct the usage_id and definition_id for the block.

    Returns:
        XBlock: The fully instantiated :class:`~xblock.core.XBlock`.

    """
    node = etree.fromstring(xml_data)
    raw_class = system.load_block_type(node.tag)
    xblock_class = system.mixologist.mix(raw_class)

    # leave next line commented out - useful for low-level debugging
    # log.debug('[create_block_from_xml] tag=%s, class=%s' % (node.tag, xblock_class))

    block_type = node.tag
    url_name = node.get('url_name')
    def_id = id_generator.create_definition(block_type, url_name)
    usage_id = id_generator.create_usage(def_id)

    scope_ids = ScopeIds(None, block_type, def_id, usage_id)
    xblock = xblock_class.parse_xml(node, system, scope_ids, id_generator)

    _convert_reference_fields_to_keys(xblock)

    return xblock


class ParentTracker(object):
    """A simple class to factor out the logic for tracking location parent pointers."""
    def __init__(self):
        """
        Init
        """
        # location -> parent.  Not using defaultdict because we care about the empty case.
        self._parents = dict()

    def add_parent(self, child, parent):
        """
        Add a parent of child location to the set of parents.  Duplicate calls have no effect.

        child and parent must be :class:`.Location` instances.
        """
        self._parents[child] = parent

    def is_known(self, child):
        """
        returns True iff child has some parents.
        """
        return child in self._parents

    def make_known(self, location):
        """Tell the parent tracker about an object, without registering any
        parents for it.  Used for the top level course descriptor locations."""
        self._parents.setdefault(location, None)

    def parent(self, child):
        """
        Return the parent of this child.  If not is_known(child), will throw a KeyError
        """
        return self._parents[child]


class XMLModuleStore(ModuleStoreReadBase):
    """
    An XML backed ModuleStore
    """
    def __init__(
        self, data_dir, default_class=None, course_dirs=None, course_ids=None,
        load_error_modules=True, i18n_service=None, **kwargs
    ):
        """
        Initialize an XMLModuleStore from data_dir

        Args:
            data_dir (str): path to data directory containing the course directories

            default_class (str): dot-separated string defining the default descriptor
                class to use if none is specified in entry_points

            course_dirs or course_ids (list of str): If specified, the list of course_dirs or course_ids to load. Otherwise,
                load all courses. Note, providing both
        """
        super(XMLModuleStore, self).__init__(**kwargs)

        self.data_dir = path(data_dir)
        self.modules = defaultdict(dict)  # course_id -> dict(location -> XBlock)
        self.courses = {}  # course_dir -> XBlock for the course
        self.errored_courses = {}  # course_dir -> errorlog, for dirs that failed to load

        if course_ids is not None:
            course_ids = [SlashSeparatedCourseKey.from_deprecated_string(course_id) for course_id in course_ids]

        self.load_error_modules = load_error_modules

        if default_class is None:
            self.default_class = None
        else:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_

        self.parent_trackers = defaultdict(ParentTracker)

        # All field data will be stored in an inheriting field data.
        self.field_data = inheriting_field_data(kvs=DictKeyValueStore())

        self.i18n_service = i18n_service

        # If we are specifically asked for missing courses, that should
        # be an error.  If we are asked for "all" courses, find the ones
        # that have a course.xml. We sort the dirs in alpha order so we always
        # read things in the same order (OS differences in load order have
        # bitten us in the past.)
        if course_dirs is None:
            course_dirs = sorted([d for d in os.listdir(self.data_dir) if
                                  os.path.exists(self.data_dir / d / "course.xml")])
        for course_dir in course_dirs:
            self.try_load_course(course_dir, course_ids)

    def try_load_course(self, course_dir, course_ids=None):
        '''
        Load a course, keeping track of errors as we go along. If course_ids is not None,
        then reject the course unless it's id is in course_ids.
        '''
        # Special-case code here, since we don't have a location for the
        # course before it loads.
        # So, make a tracker to track load-time errors, then put in the right
        # place after the course loads and we have its location
        errorlog = make_error_tracker()
        course_descriptor = None
        try:
            course_descriptor = self.load_course(course_dir, course_ids, errorlog.tracker)
        except Exception as exc:  # pylint: disable=broad-except
            msg = "ERROR: Failed to load course '{0}': {1}".format(
                course_dir.encode("utf-8"), unicode(exc)
            )
            log.exception(msg)
            errorlog.tracker(msg)
            self.errored_courses[course_dir] = errorlog

        if course_descriptor is None:
            pass
        elif isinstance(course_descriptor, ErrorDescriptor):
            # Didn't load course.  Instead, save the errors elsewhere.
            self.errored_courses[course_dir] = errorlog
        else:
            self.courses[course_dir] = course_descriptor
            self._course_errors[course_descriptor.id] = errorlog
            self.parent_trackers[course_descriptor.id].make_known(course_descriptor.scope_ids.usage_id)

    def __unicode__(self):
        '''
        String representation - for debugging
        '''
        return '<XMLModuleStore data_dir=%r, %d courses, %d modules>' % (
            self.data_dir, len(self.courses), len(self.modules)
        )

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

    def load_course(self, course_dir, course_ids, tracker):
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

            course_id = SlashSeparatedCourseKey(org, course, url_name)
            if course_ids is not None and course_id not in course_ids:
                return None

            def get_policy(usage_id):
                """
                Return the policy dictionary to be applied to the specified XBlock usage
                """
                return policy.get(policy_key(usage_id), {})

            services = {}
            if self.i18n_service:
                services['i18n'] = self.i18n_service

            system = ImportSystem(
                xmlstore=self,
                course_id=course_id,
                course_dir=course_dir,
                error_tracker=tracker,
                parent_tracker=self.parent_trackers[course_id],
                load_error_modules=self.load_error_modules,
                get_policy=get_policy,
                mixins=self.xblock_mixins,
                default_class=self.default_class,
                select=self.xblock_select,
                field_data=self.field_data,
                services=services,
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

    def _import_field_content(self, course_descriptor, category, file_path):
        """
        Import field data content for field other than 'data' or 'metadata' form json file and
        return field data content as dictionary
        """
        slug, location, data_content = None, None, None
        try:
            # try to read json file
            # file_path format: {dirname}.{field_name}.json
            dirname, field, file_suffix = file_path.split('/')[-1].split('.')
            if file_suffix == 'json' and field not in DEFAULT_CONTENT_FIELDS:
                slug = os.path.splitext(os.path.basename(dirname))[0]
                location = course_descriptor.scope_ids.usage_id.replace(category=category, name=slug)
                with open(file_path) as field_content_file:
                    field_data = json.load(field_content_file)
                    data_content = {field: field_data}
        except (IOError, ValueError):
            # ignore this exception
            # only new exported courses which use content fields other than 'metadata' and 'data'
            # will have this file '{dirname}.{field_name}.json'
            data_content = None

        return slug, location, data_content

    def _load_extra_content(self, system, course_descriptor, category, content_path, course_dir):
        """
        Import fields data content from files
        """
        for filepath in glob.glob(content_path / '*'):
            if not os.path.isfile(filepath):
                continue

            if filepath.endswith('~'):  # skip *~ files
                continue

            with open(filepath) as f:
                try:
                    if filepath.find('.json') != -1:
                        # json file with json data content
                        slug, loc, data_content = self._import_field_content(course_descriptor, category, filepath)
                        if data_content is None:
                            continue
                        else:
                            try:
                                # get and update data field in xblock runtime
                                module = system.load_item(loc)
                                for key, value in data_content.iteritems():
                                    setattr(module, key, value)
                                module.save()
                            except ItemNotFoundError:
                                module = None
                                data_content['location'] = loc
                                data_content['category'] = category
                    else:
                        slug = os.path.splitext(os.path.basename(filepath))[0]
                        loc = course_descriptor.scope_ids.usage_id.replace(category=category, name=slug)
                        # html file with html data content
                        html = f.read().decode('utf-8')
                        try:
                            module = system.load_item(loc)
                            module.data = html
                            module.save()
                        except ItemNotFoundError:
                            module = None
                            data_content = {'data': html, 'location': loc, 'category': category}

                    if module is None:
                        module = system.construct_xblock(
                            category,
                            # We're loading a descriptor, so student_id is meaningless
                            # We also don't have separate notions of definition and usage ids yet,
                            # so we use the location for both
                            ScopeIds(None, category, loc, loc),
                            DictFieldData(data_content),
                        )
                        # VS[compat]:
                        # Hack because we need to pull in the 'display_name' for static tabs (because we need to edit them)
                        # from the course policy
                        if category == "static_tab":
                            tab = CourseTabList.get_tab_by_slug(tab_list=course_descriptor.tabs, url_slug=slug)
                            if tab:
                                module.display_name = tab.name
                        module.data_dir = course_dir
                        module.save()

                        self.modules[course_descriptor.id][module.scope_ids.usage_id] = module
                except Exception as exc:  # pylint: disable=broad-except
                    logging.exception("Failed to load %s. Skipping... \
                            Exception: %s", filepath, unicode(exc))
                    system.error_tracker("ERROR: " + unicode(exc))

    def has_item(self, usage_key):
        """
        Returns True if location exists in this ModuleStore.
        """
        return usage_key in self.modules[usage_key.course_key]

    def get_item(self, usage_key, depth=0, **kwargs):
        """
        Returns an XBlock instance for the item for this UsageKey.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        usage_key: a UsageKey that matches the module we are looking for.
        """
        try:
            return self.modules[usage_key.course_key][usage_key]
        except KeyError:
            raise ItemNotFoundError(usage_key)

    def get_items(self, course_id, settings=None, content=None, revision=None, qualifiers=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_id

        NOTE: don't use this to look for courses
        as the course_id is required. Use get_courses.

        Args:
            course_id (CourseKey): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as qualifiers below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as qualifiers below.
            qualifiers (dict): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                Substring matching pass a regex object.
                For this modulestore, ``name`` is another commonly provided key (Location based stores)
                (but not revision!)
                For this modulestore,
                you can search dates by providing either a datetime for == (probably
                useless) or a tuple (">"|"<" datetime) for after or before, etc.
        """
        if revision == ModuleStoreEnum.RevisionOption.draft_only:
            return []

        items = []

        qualifiers = qualifiers.copy() if qualifiers else {}  # copy the qualifiers (destructively manipulated here)
        category = qualifiers.pop('category', None)
        name = qualifiers.pop('name', None)

        def _block_matches_all(mod_loc, module):
            if category and mod_loc.category != category:
                return False
            if name and mod_loc.name != name:
                return False
            return all(
                self._block_matches(module, fields or {})
                for fields in [settings, content, qualifiers]
            )

        for mod_loc, module in self.modules[course_id].iteritems():
            if _block_matches_all(mod_loc, module):
                items.append(module)

        return items

    def make_course_key(self, org, course, run):
        """
        Return a valid :class:`~opaque_keys.edx.keys.CourseKey` for this modulestore
        that matches the supplied `org`, `course`, and `run`.

        This key may represent a course that doesn't exist in this modulestore.
        """
        return CourseLocator(org, course, run, deprecated=True)

    def get_courses(self, depth=0, **kwargs):
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

    def get_orphans(self, course_key, **kwargs):
        """
        Get all of the xblocks in the given course which have no parents and are not of types which are
        usually orphaned. NOTE: may include xblocks which still have references via xblocks which don't
        use children to point to their dependents.
        """
        # here just to quell the abstractmethod. someone could write the impl if needed
        raise NotImplementedError

    def get_parent_location(self, location, **kwargs):
        '''Find the location that is the parent of this location in this
        course.  Needed for path_to_location().
        '''
        if not self.parent_trackers[location.course_key].is_known(location):
            raise ItemNotFoundError("{0} not in {1}".format(location, location.course_key))

        return self.parent_trackers[location.course_key].parent(location)

    def get_modulestore_type(self, course_key=None):
        """
        Returns an enumeration-like type reflecting the type of this modulestore, per ModuleStoreEnum.Type
        Args:
            course_key: just for signature compatibility
        """
        return ModuleStoreEnum.Type.xml

    def get_courses_for_wiki(self, wiki_slug, **kwargs):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course locations
        """
        courses = self.get_courses()
        return [course.location.course_key for course in courses if (course.wiki_slug == wiki_slug)]

    def heartbeat(self):
        """
        Ensure that every known course is loaded and ready to go. Really, just return b/c
        if this gets called the __init__ finished which means the courses are loaded.

        Returns the course count
        """
        return {ModuleStoreEnum.Type.xml: True}

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):  # pylint: disable=unused-argument
        """
        A context manager for temporarily setting the branch value for the store to the given branch_setting.
        """
        if branch_setting != ModuleStoreEnum.Branch.published_only:
            raise ValueError(u"Cannot set branch setting to {} on a ReadOnly store".format(branch_setting))
        yield
