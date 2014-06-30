# -*- coding: utf-8 -*-

import datetime
import ddt
import unittest

from fs.memoryfs import MemoryFS
from lxml import etree
from mock import Mock, patch

from django.utils.timezone import UTC

from xmodule.xml_module import is_pointer_tag
from opaque_keys.edx.locations import Location
from xmodule.modulestore import only_xmodules
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore
from xmodule.modulestore.inheritance import compute_inherited_metadata
from xmodule.x_module import XModuleMixin
from xmodule.fields import Date
from xmodule.tests import DATA_DIR
from xmodule.modulestore.inheritance import InheritanceMixin
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer
from xblock.runtime import KvsFieldData, DictKeyValueStore


ORG = 'test_org'
COURSE = 'test_course'


class DummySystem(ImportSystem):

    @patch('xmodule.modulestore.xml.OSFS', lambda dir: MemoryFS())
    def __init__(self, load_error_modules):

        xmlstore = XMLModuleStore("data_dir", course_dirs=[], load_error_modules=load_error_modules)
        course_id = SlashSeparatedCourseKey(ORG, COURSE, 'test_run')
        course_dir = "test_dir"
        error_tracker = Mock()
        parent_tracker = Mock()

        super(DummySystem, self).__init__(
            xmlstore=xmlstore,
            course_id=course_id,
            course_dir=course_dir,
            error_tracker=error_tracker,
            parent_tracker=parent_tracker,
            load_error_modules=load_error_modules,
            mixins=(InheritanceMixin, XModuleMixin),
            field_data=KvsFieldData(DictKeyValueStore()),
        )

    def render_template(self, _template, _context):
        raise Exception("Shouldn't be called")


class BaseCourseTestCase(unittest.TestCase):
    '''Make sure module imports work properly, including for malformed inputs'''
    @staticmethod
    def get_system(load_error_modules=True):
        '''Get a dummy system'''
        return DummySystem(load_error_modules)

    def get_course(self, name):
        """Get a test course by directory name.  If there's more than one, error."""
        print("Importing {0}".format(name))

        modulestore = XMLModuleStore(
            DATA_DIR,
            course_dirs=[name],
            xblock_mixins=(InheritanceMixin,),
            xblock_select=only_xmodules,
        )
        courses = modulestore.get_courses()
        self.assertEquals(len(courses), 1)
        return courses[0]


class GenericXBlock(XBlock):
    """XBlock for testing pure xblock xml import"""
    has_children = True
    field1 = String(default="something", scope=Scope.user_state)
    field2 = Integer(scope=Scope.user_state)


@ddt.ddt
class PureXBlockImportTest(BaseCourseTestCase):
    """
    Tests of import pure XBlocks (not XModules) from xml
    """

    def assert_xblocks_are_good(self, block):
        """Assert a number of conditions that must be true for `block` to be good."""
        scope_ids = block.scope_ids
        self.assertIsNotNone(scope_ids.usage_id)
        self.assertIsNotNone(scope_ids.def_id)

        for child_id in block.children:
            child = block.runtime.get_block(child_id)
            self.assert_xblocks_are_good(child)

    @XBlock.register_temp_plugin(GenericXBlock)
    @ddt.data(
        "<genericxblock/>",
        "<genericxblock field1='abc' field2='23' />",
        "<genericxblock field1='abc' field2='23'><genericxblock/></genericxblock>",
    )
    @patch('xmodule.x_module.XModuleMixin.location')
    def test_parsing_pure_xblock(self, xml, mock_location):
        system = self.get_system(load_error_modules=False)
        descriptor = system.process_xml(xml)
        self.assertIsInstance(descriptor, GenericXBlock)
        self.assert_xblocks_are_good(descriptor)
        self.assertFalse(mock_location.called)


class ImportTestCase(BaseCourseTestCase):
    date = Date()

    def test_fallback(self):
        '''Check that malformed xml loads as an ErrorDescriptor.'''

        # Use an exotic character to also flush out Unicode issues.
        bad_xml = u'''<sequential display_name="oops\N{SNOWMAN}"><video url="hi"></sequential>'''
        system = self.get_system()

        descriptor = system.process_xml(bad_xml)

        self.assertEqual(descriptor.__class__.__name__, 'ErrorDescriptorWithMixins')

    def test_unique_url_names(self):
        '''Check that each error gets its very own url_name'''
        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        bad_xml2 = '''<sequential url_name="oops"><video url="hi"></sequential>'''
        system = self.get_system()

        descriptor1 = system.process_xml(bad_xml)
        descriptor2 = system.process_xml(bad_xml2)

        self.assertNotEqual(descriptor1.location, descriptor2.location)

        # Check that each vertical gets its very own url_name
        bad_xml = '''<vertical display_name="abc"><problem url_name="exam1:2013_Spring:abc"/></vertical>'''
        bad_xml2 = '''<vertical display_name="abc"><problem url_name="exam2:2013_Spring:abc"/></vertical>'''

        descriptor1 = system.process_xml(bad_xml)
        descriptor2 = system.process_xml(bad_xml2)

        self.assertNotEqual(descriptor1.location, descriptor2.location)


    def test_reimport(self):
        '''Make sure an already-exported error xml tag loads properly'''

        self.maxDiff = None
        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        system = self.get_system()
        descriptor = system.process_xml(bad_xml)

        node = etree.Element('unknown')
        descriptor.add_xml_to_node(node)
        re_import_descriptor = system.process_xml(etree.tostring(node))

        self.assertEqual(re_import_descriptor.__class__.__name__, 'ErrorDescriptorWithMixins')

        self.assertEqual(descriptor.contents, re_import_descriptor.contents)
        self.assertEqual(descriptor.error_msg, re_import_descriptor.error_msg)

    def test_fixed_xml_tag(self):
        """Make sure a tag that's been fixed exports as the original tag type"""

        # create a error tag with valid xml contents
        root = etree.Element('error')
        good_xml = '''<sequential display_name="fixed"><video url="hi"/></sequential>'''
        root.text = good_xml

        xml_str_in = etree.tostring(root)

        # load it
        system = self.get_system()
        descriptor = system.process_xml(xml_str_in)

        # export it
        node = etree.Element('unknown')
        descriptor.add_xml_to_node(node)

        # Now make sure the exported xml is a sequential
        self.assertEqual(node.tag, 'sequential')

    def test_metadata_import_export(self):
        """Two checks:
            - unknown metadata is preserved across import-export
            - inherited metadata doesn't leak to children.
        """
        system = self.get_system()
        v = 'March 20 17:00'
        url_name = 'test1'
        start_xml = '''
        <course org="{org}" course="{course}"
                due="{due}" url_name="{url_name}" unicorn="purple">
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
        </course>'''.format(due=v, org=ORG, course=COURSE, url_name=url_name)
        descriptor = system.process_xml(start_xml)
        compute_inherited_metadata(descriptor)

        # pylint: disable=W0212
        print(descriptor, descriptor._field_data)
        self.assertEqual(descriptor.due, ImportTestCase.date.from_json(v))

        # Check that the child inherits due correctly
        child = descriptor.get_children()[0]
        self.assertEqual(child.due, ImportTestCase.date.from_json(v))
        # need to convert v to canonical json b4 comparing
        self.assertEqual(
            ImportTestCase.date.to_json(ImportTestCase.date.from_json(v)),
            child.xblock_kvs.inherited_settings['due']
        )

        # Now export and check things
        descriptor.runtime.export_fs = MemoryFS()
        node = etree.Element('unknown')
        descriptor.add_xml_to_node(node)

        # Check that the exported xml is just a pointer
        print("Exported xml:", etree.tostring(node))
        self.assertTrue(is_pointer_tag(node))
        # but it's a special case course pointer
        self.assertEqual(node.attrib['course'], COURSE)
        self.assertEqual(node.attrib['org'], ORG)

        # Does the course still have unicorns?
        with descriptor.runtime.export_fs.open('course/{url_name}.xml'.format(url_name=url_name)) as f:
            course_xml = etree.fromstring(f.read())

        self.assertEqual(course_xml.attrib['unicorn'], 'purple')

        # the course and org tags should be _only_ in the pointer
        self.assertTrue('course' not in course_xml.attrib)
        self.assertTrue('org' not in course_xml.attrib)

        # did we successfully strip the url_name from the definition contents?
        self.assertTrue('url_name' not in course_xml.attrib)

        # Does the chapter tag now have a due attribute?
        # hardcoded path to child
        with descriptor.runtime.export_fs.open('chapter/ch.xml') as f:
            chapter_xml = etree.fromstring(f.read())
        self.assertEqual(chapter_xml.tag, 'chapter')
        self.assertFalse('due' in chapter_xml.attrib)

    def test_metadata_no_inheritance(self):
        """
        Checks that default value of None (for due) does not get marked as inherited.
        """
        system = self.get_system()
        url_name = 'test1'
        start_xml = '''
        <course org="{org}" course="{course}"
                url_name="{url_name}" unicorn="purple">
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
        </course>'''.format(org=ORG, course=COURSE, url_name=url_name)
        descriptor = system.process_xml(start_xml)
        compute_inherited_metadata(descriptor)

        self.assertEqual(descriptor.due, None)

        # Check that the child does not inherit a value for due
        child = descriptor.get_children()[0]
        self.assertEqual(child.due, None)

        # Check that the child hasn't started yet
        self.assertLessEqual(
            datetime.datetime.now(UTC()),
            child.start
        )

    def test_metadata_override_default(self):
        """
        Checks that due date can be overriden at child level.
        """
        system = self.get_system()
        course_due = 'March 20 17:00'
        child_due = 'April 10 00:00'
        url_name = 'test1'
        start_xml = '''
        <course org="{org}" course="{course}"
                due="{due}" url_name="{url_name}" unicorn="purple">
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
        </course>'''.format(due=course_due, org=ORG, course=COURSE, url_name=url_name)
        descriptor = system.process_xml(start_xml)
        child = descriptor.get_children()[0]
        # pylint: disable=W0212
        child._field_data.set(child, 'due', child_due)
        compute_inherited_metadata(descriptor)

        self.assertEqual(descriptor.due, ImportTestCase.date.from_json(course_due))
        self.assertEqual(child.due, ImportTestCase.date.from_json(child_due))
        # Test inherited metadata. Due does not appear here (because explicitly set on child).
        self.assertEqual(
            ImportTestCase.date.to_json(ImportTestCase.date.from_json(course_due)),
            child.xblock_kvs.inherited_settings['due']
        )

    def test_is_pointer_tag(self):
        """
        Check that is_pointer_tag works properly.
        """

        yes = ["""<html url_name="blah"/>""",
               """<html url_name="blah"></html>""",
               """<html url_name="blah">    </html>""",
               """<problem url_name="blah"/>""",
               """<course org="HogwartsX" course="Mathemagics" url_name="3.14159"/>"""]

        no = ["""<html url_name="blah" also="this"/>""",
              """<html url_name="blah">some text</html>""",
              """<problem url_name="blah"><sub>tree</sub></problem>""",
              """<course org="HogwartsX" course="Mathemagics" url_name="3.14159">
                     <chapter>3</chapter>
                  </course>
              """]

        for xml_str in yes:
            print("should be True for {0}".format(xml_str))
            self.assertTrue(is_pointer_tag(etree.fromstring(xml_str)))

        for xml_str in no:
            print("should be False for {0}".format(xml_str))
            self.assertFalse(is_pointer_tag(etree.fromstring(xml_str)))

    def test_metadata_inherit(self):
        """Make sure that metadata is inherited properly"""

        print("Starting import")
        course = self.get_course('toy')

        def check_for_key(key, node, value):
            "recursive check for presence of key"
            print("Checking {0}".format(node.location.to_deprecated_string()))
            self.assertEqual(getattr(node, key), value)
            for c in node.get_children():
                check_for_key(key, c, value)

        check_for_key('graceperiod', course, course.graceperiod)

    def test_policy_loading(self):
        """Make sure that when two courses share content with the same
        org and course names, policy applies to the right one."""

        toy = self.get_course('toy')
        two_toys = self.get_course('two_toys')

        self.assertEqual(toy.url_name, "2012_Fall")
        self.assertEqual(two_toys.url_name, "TT_2012_Fall")

        toy_ch = toy.get_children()[0]
        two_toys_ch = two_toys.get_children()[0]

        self.assertEqual(toy_ch.display_name, "Overview")
        self.assertEqual(two_toys_ch.display_name, "Two Toy Overview")

        # Also check that the grading policy loaded
        self.assertEqual(two_toys.grade_cutoffs['C'], 0.5999)

        # Also check that keys from policy are run through the
        # appropriate attribute maps -- 'graded' should be True, not 'true'
        self.assertEqual(toy.graded, True)

    def test_definition_loading(self):
        """When two courses share the same org and course name and
        both have a module with the same url_name, the definitions shouldn't clash.

        TODO (vshnayder): once we have a CMS, this shouldn't
        happen--locations should uniquely name definitions.  But in
        our imperfect XML world, it can (and likely will) happen."""

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy', 'two_toys'])

        location = Location("edX", "toy", "2012_Fall", "video", "Welcome", None)
        toy_video = modulestore.get_item(location)
        location_two = Location("edX", "toy", "TT_2012_Fall", "video", "Welcome", None)
        two_toy_video = modulestore.get_item(location_two)
        self.assertEqual(toy_video.youtube_id_1_0, "p2Q6BrNhdh8")
        self.assertEqual(two_toy_video.youtube_id_1_0, "p2Q6BrNhdh9")

    def test_colon_in_url_name(self):
        """Ensure that colons in url_names convert to file paths properly"""

        print("Starting import")
        # Not using get_courses because we need the modulestore object too afterward
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'])
        courses = modulestore.get_courses()
        self.assertEquals(len(courses), 1)
        course = courses[0]

        print("course errors:")
        for (msg, err) in modulestore.get_course_errors(course.id):
            print(msg)
            print(err)

        chapters = course.get_children()
        self.assertEquals(len(chapters), 5)

        ch2 = chapters[1]
        self.assertEquals(ch2.url_name, "secret:magic")

        print("Ch2 location: ", ch2.location)

        also_ch2 = modulestore.get_item(ch2.location)
        self.assertEquals(ch2, also_ch2)

        print("making sure html loaded")
        loc = course.id.make_usage_key('html', 'secret:toylab')
        html = modulestore.get_item(loc)
        self.assertEquals(html.display_name, "Toy lab")

    def test_unicode(self):
        """Check that courses with unicode characters in filenames and in
        org/course/name import properly. Currently, this means: (a) Having
        files with unicode names does not prevent import; (b) if files are not
        loaded because of unicode filenames, there are appropriate
        exceptions/errors to that effect."""

        print("Starting import")
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['test_unicode'])
        courses = modulestore.get_courses()
        self.assertEquals(len(courses), 1)
        course = courses[0]

        print("course errors:")

        # Expect to find an error/exception about characters in "®esources"
        expect = "UnicodeEncodeError"
        errors = [
            (msg.encode("utf-8"), err.encode("utf-8"))
            for msg, err
            in modulestore.get_course_errors(course.id)
        ]
        for msg, err in errors:
            print("msg: " + str(msg))
            print("err: " + str(err))

        self.assertTrue(any(
            expect in msg or expect in err
            for msg, err in errors
        ))
        chapters = course.get_children()
        self.assertEqual(len(chapters), 4)

    def test_url_name_mangling(self):
        """
        Make sure that url_names are only mangled once.
        """

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'])

        toy_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        course = modulestore.get_course(toy_id)
        chapters = course.get_children()
        ch1 = chapters[0]
        sections = ch1.get_children()

        self.assertEqual(len(sections), 4)

        for i in (2, 3):
            video = sections[i]
            # Name should be 'video_{hash}'
            print("video {0} url_name: {1}".format(i, video.url_name))

            self.assertEqual(len(video.url_name), len('video_') + 12)

    def test_poll_and_conditional_import(self):
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['conditional_and_poll'])

        course = modulestore.get_courses()[0]
        chapters = course.get_children()
        ch1 = chapters[0]
        sections = ch1.get_children()

        self.assertEqual(len(sections), 1)

        conditional_location = course.id.make_usage_key('conditional', 'condone')
        module = modulestore.get_item(conditional_location)
        self.assertEqual(len(module.children), 1)

        poll_location = course.id.make_usage_key('poll_question', 'first_poll')
        module = modulestore.get_item(poll_location)
        self.assertEqual(len(module.get_children()), 0)
        self.assertEqual(module.voted, False)
        self.assertEqual(module.poll_answer, '')
        self.assertEqual(module.poll_answers, {})
        self.assertEqual(
            module.answers,
            [
                {'text': u'Yes', 'id': 'Yes'},
                {'text': u'No', 'id': 'No'},
                {'text': u"Don't know", 'id': 'Dont_know'}
            ]
        )

    def test_error_on_import(self):
        '''Check that when load_error_module is false, an exception is raised, rather than returning an ErrorModule'''

        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        system = self.get_system(False)

        self.assertRaises(etree.XMLSyntaxError, system.process_xml, bad_xml)

    def test_graphicslidertool_import(self):
        '''
        Check to see if definition_from_xml in gst_module.py
        works properly.  Pulls data from the graphic_slider_tool directory
        in the test data directory.
        '''
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['graphic_slider_tool'])

        sa_id = SlashSeparatedCourseKey("edX", "gst_test", "2012_Fall")
        location = sa_id.make_usage_key("graphical_slider_tool", "sample_gst")
        gst_sample = modulestore.get_item(location)
        render_string_from_sample_gst_xml = """
        <slider var="a" style="width:400px;float:left;"/>\
<plot style="margin-top:15px;margin-bottom:15px;"/>""".strip()
        self.assertIn(render_string_from_sample_gst_xml, gst_sample.data)

    def test_word_cloud_import(self):
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['word_cloud'])

        course = modulestore.get_courses()[0]
        chapters = course.get_children()
        ch1 = chapters[0]
        sections = ch1.get_children()

        self.assertEqual(len(sections), 1)

        location = course.id.make_usage_key('word_cloud', 'cloud1')
        module = modulestore.get_item(location)
        self.assertEqual(len(module.get_children()), 0)
        self.assertEqual(module.num_inputs, 5)
        self.assertEqual(module.num_top_words, 250)

    def test_cohort_config(self):
        """
        Check that cohort config parsing works right.
        """
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'])

        toy_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        course = modulestore.get_course(toy_id)

        # No config -> False
        self.assertFalse(course.is_cohorted)

        # empty config -> False
        course.cohort_config = {}
        self.assertFalse(course.is_cohorted)

        # false config -> False
        course.cohort_config = {'cohorted': False}
        self.assertFalse(course.is_cohorted)

        # and finally...
        course.cohort_config = {'cohorted': True}
        self.assertTrue(course.is_cohorted)
