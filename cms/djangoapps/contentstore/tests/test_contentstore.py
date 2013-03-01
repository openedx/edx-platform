import json
import shutil
from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from path import path
from tempdir import mkdtemp_clean
import json
from fs.osfs import OSFS
import copy
from mock import Mock
from json import dumps, loads

from student.models import Registration
from django.contrib.auth.models import User
from cms.djangoapps.contentstore.utils import get_modulestore

from utils import ModuleStoreTestCase, parse_json
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from xmodule.modulestore import Location
from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.store_utilities import delete_course
from xmodule.modulestore.django import modulestore, _MODULESTORES
from xmodule.contentstore.django import contentstore
from xmodule.templates import update_templates
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.templates import update_templates

from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.seq_module import SequenceDescriptor
from xmodule.modulestore.exceptions import ItemNotFoundError

TEST_DATA_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
TEST_DATA_MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
TEST_DATA_MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')


@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class ContentStoreToyCourseTest(ModuleStoreTestCase):
    """
    Tests that rely on the toy courses.
    TODO: refactor using CourseFactory so they do not.
    """
    def setUp(self):
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.client = Client()
        self.client.login(username=uname, password=password)


    def check_edit_unit(self, test_course_name):
        import_from_xml(modulestore(), 'common/test/data/', [test_course_name])

        for descriptor in modulestore().get_items(Location(None, None, 'vertical', None, None)):
            print "Checking ", descriptor.location.url()
            print descriptor.__class__, descriptor.location
            resp = self.client.get(reverse('edit_unit', kwargs={'location': descriptor.location.url()}))
            self.assertEqual(resp.status_code, 200)

    def test_edit_unit_toy(self):
        self.check_edit_unit('toy')

    def test_edit_unit_full(self):
        self.check_edit_unit('full')

    def test_static_tab_reordering(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        ms = modulestore('direct')
        course = ms.get_item(Location(['i4x', 'edX', 'full', 'course', '6.002_Spring_2012', None]))

        # reverse the ordering
        reverse_tabs = []
        for tab in course.tabs:
            if tab['type'] == 'static_tab':
                reverse_tabs.insert(0, 'i4x://edX/full/static_tab/{0}'.format(tab['url_slug']))

        resp = self.client.post(reverse('reorder_static_tabs'), json.dumps({'tabs': reverse_tabs}), "application/json")

        course = ms.get_item(Location(['i4x', 'edX', 'full', 'course', '6.002_Spring_2012', None]))

        # compare to make sure that the tabs information is in the expected order after the server call
        course_tabs = []
        for tab in course.tabs:
            if tab['type'] == 'static_tab':
                course_tabs.append('i4x://edX/full/static_tab/{0}'.format(tab['url_slug']))

        self.assertEqual(reverse_tabs, course_tabs)

    def test_about_overrides(self):
        '''
        This test case verifies that a course can use specialized override for about data, e.g. /about/Fall_2012/effort.html
        while there is a base definition in /about/effort.html
        '''
        import_from_xml(modulestore(), 'common/test/data/', ['full'])
        ms = modulestore('direct')
        effort = ms.get_item(Location(['i4x', 'edX', 'full', 'about', 'effort', None]))
        self.assertEqual(effort.definition['data'], '6 hours')

        # this one should be in a non-override folder
        effort = ms.get_item(Location(['i4x', 'edX', 'full', 'about', 'end_date', None]))
        self.assertEqual(effort.definition['data'], 'TBD')

    def test_remove_hide_progress_tab(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        ms = modulestore('direct')
        cs = contentstore()

        source_location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')
        course = ms.get_item(source_location)
        self.assertNotIn('hide_progress_tab', course.metadata)

    def test_clone_course(self):

        course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }

        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        resp = self.client.post(reverse('create_new_course'), course_data)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['id'], 'i4x://MITx/999/course/Robot_Super_Course')

        ms = modulestore('direct')
        cs = contentstore()

        source_location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')
        dest_location = CourseDescriptor.id_to_location('MITx/999/Robot_Super_Course')

        clone_course(ms, cs, source_location, dest_location)

        # now loop through all the units in the course and verify that the clone can render them, which
        # means the objects are at least present
        items = ms.get_items(Location(['i4x', 'edX', 'full', 'vertical', None]))
        self.assertGreater(len(items), 0)
        clone_items = ms.get_items(Location(['i4x', 'MITx', '999', 'vertical', None]))
        self.assertGreater(len(clone_items), 0)
        for descriptor in items:
            new_loc = descriptor.location._replace(org='MITx', course='999')
            print "Checking {0} should now also be at {1}".format(descriptor.location.url(), new_loc.url())
            resp = self.client.get(reverse('edit_unit', kwargs={'location': new_loc.url()}))
            self.assertEqual(resp.status_code, 200)

    def test_delete_course(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        ms = modulestore('direct')
        cs = contentstore()

        location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')

        delete_course(ms, cs, location)

        items = ms.get_items(Location(['i4x', 'edX', 'full', 'vertical', None]))
        self.assertEqual(len(items), 0)

    def verify_content_existence(self, modulestore, root_dir, location, dirname, category_name, filename_suffix=''):
        fs = OSFS(root_dir / 'test_export')
        self.assertTrue(fs.exists(dirname))

        query_loc = Location('i4x', location.org, location.course, category_name, None)
        items = modulestore.get_items(query_loc)

        for item in items:
            fs = OSFS(root_dir / ('test_export/' + dirname))
            self.assertTrue(fs.exists(item.location.name + filename_suffix))

    def test_export_course(self):
        ms = modulestore('direct')
        cs = contentstore()

        import_from_xml(ms, 'common/test/data/', ['full'])
        location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(ms, cs, location, root_dir, 'test_export')

        # check for static tabs
        self.verify_content_existence(ms, root_dir, location, 'tabs', 'static_tab', '.html')

        # check for custom_tags
        self.verify_content_existence(ms, root_dir, location, 'info', 'course_info', '.html')

        # check for custom_tags
        self.verify_content_existence(ms, root_dir, location, 'custom_tags', 'custom_tag_template')

        # check for graiding_policy.json
        fs = OSFS(root_dir / 'test_export/policies/6.002_Spring_2012')
        self.assertTrue(fs.exists('grading_policy.json'))

        course = ms.get_item(location)
        # compare what's on disk compared to what we have in our course
        with fs.open('grading_policy.json','r') as grading_policy:
            on_disk = loads(grading_policy.read())    
            self.assertEqual(on_disk, course.definition['data']['grading_policy'])

        #check for policy.json
        self.assertTrue(fs.exists('policy.json'))

        # compare what's on disk to what we have in the course module
        with fs.open('policy.json','r') as course_policy:
            on_disk = loads(course_policy.read())
            self.assertIn('course/6.002_Spring_2012', on_disk)
            self.assertEqual(on_disk['course/6.002_Spring_2012'], course.metadata)

        # remove old course
        delete_course(ms, cs, location)

        # reimport
        import_from_xml(ms, root_dir, ['test_export'])

        items = ms.get_items(Location(['i4x', 'edX', 'full', 'vertical', None]))
        self.assertGreater(len(items), 0)
        for descriptor in items:
            print "Checking {0}....".format(descriptor.location.url())
            resp = self.client.get(reverse('edit_unit', kwargs={'location': descriptor.location.url()}))
            self.assertEqual(resp.status_code, 200)

        shutil.rmtree(root_dir)

    def test_course_handouts_rewrites(self):
        ms = modulestore('direct')
        cs = contentstore()

        # import a test course
        import_from_xml(ms, 'common/test/data/', ['full'])

        handout_location = Location(['i4x', 'edX', 'full', 'course_info', 'handouts'])

        # get module info
        resp = self.client.get(reverse('module_info', kwargs={'module_location': handout_location}))

        # make sure we got a successful response
        self.assertEqual(resp.status_code, 200)

        # check that /static/ has been converted to the full path
        # note, we know the link it should be because that's what in the 'full' course in the test data
        self.assertContains(resp, '/c4x/edX/full/asset/handouts_schematic_tutorial.pdf')



class ContentStoreTest(ModuleStoreTestCase):
    """
    Tests for the CMS ContentStore application.
    """
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.client = Client()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }

    def test_create_course(self):
        """Test new course creation - happy path"""
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['id'], 'i4x://MITx/999/course/Robot_Super_Course')

    def test_create_course_duplicate_course(self):
        """Test new course creation - error path"""
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        data = parse_json(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['ErrMsg'], 'There is already a course defined with this name.')

    def test_create_course_duplicate_number(self):
        """Test new course creation - error path"""
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        self.course_data['display_name'] = 'Robot Super Course Two'

        resp = self.client.post(reverse('create_new_course'), self.course_data)
        data = parse_json(resp)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['ErrMsg'],
            'There is already a course defined with the same organization and course number.')

    def test_create_course_with_bad_organization(self):
        """Test new course creation - error path for bad organization name"""
        self.course_data['org'] = 'University of California, Berkeley'
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        data = parse_json(resp)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['ErrMsg'],
            "Unable to create course 'Robot Super Course'.\n\nInvalid characters in 'University of California, Berkeley'.")

    def test_course_index_view_with_no_courses(self):
        """Test viewing the index page with no courses"""
        # Create a course so there is something to view
        resp = self.client.get(reverse('index'))
        self.assertContains(resp,
            '<h1 class="title-1">My Courses</h1>',
            status_code=200,
            html=True)

    def test_course_factory(self):
        """Test that the course factory works correctly."""
        course = CourseFactory.create()
        self.assertIsInstance(course, CourseDescriptor)

    def test_item_factory(self):
        """Test that the item factory works correctly."""
        course = CourseFactory.create()
        item = ItemFactory.create(parent_location=course.location)
        self.assertIsInstance(item, SequenceDescriptor)

    def test_course_index_view_with_course(self):
        """Test viewing the index page with an existing course"""
        CourseFactory.create(display_name='Robot Super Educational Course')
        resp = self.client.get(reverse('index'))
        self.assertContains(resp,
            '<span class="class-name">Robot Super Educational Course</span>',
            status_code=200,
            html=True)

    def test_course_overview_view_with_course(self):
        """Test viewing the course overview page with an existing course"""
        CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        data = {
                'org': 'MITx',
                'course': '999',
                'name': Location.clean('Robot Super Course'),
                }

        resp = self.client.get(reverse('course_index', kwargs=data))
        self.assertContains(resp,
            '<article class="courseware-overview" data-course-id="i4x://MITx/999/course/Robot_Super_Course">',
            status_code=200,
            html=True)

    def test_clone_item(self):
        """Test cloning an item. E.g. creating a new section"""
        CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        section_data = {
            'parent_location': 'i4x://MITx/999/course/Robot_Super_Course',
            'template': 'i4x://edx/templates/chapter/Empty',
            'display_name': 'Section One',
            }

        resp = self.client.post(reverse('clone_item'), section_data)

        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertRegexpMatches(data['id'],
            '^i4x:\/\/MITx\/999\/chapter\/([0-9]|[a-f]){32}$')

    def test_capa_module(self):
        """Test that a problem treats markdown specially."""
        course = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        problem_data = {
            'parent_location': 'i4x://MITx/999/course/Robot_Super_Course',
            'template': 'i4x://edx/templates/problem/Blank_Common_Problem'
            }

        resp = self.client.post(reverse('clone_item'), problem_data)

        self.assertEqual(resp.status_code, 200)
        payload = parse_json(resp)
        problem_loc = payload['id']
        problem = get_modulestore(problem_loc).get_item(problem_loc)
        # should be a CapaDescriptor
        self.assertIsInstance(problem, CapaDescriptor, "New problem is not a CapaDescriptor")
        context = problem.get_context()
        self.assertIn('markdown', context, "markdown is missing from context")
        self.assertIn('markdown', problem.metadata, "markdown is missing from metadata")
        self.assertNotIn('markdown', problem.editable_metadata_fields, "Markdown slipped into the editable metadata fields")

    def test_import_metadata_with_attempts_empty_string(self):
        import_from_xml(modulestore(), 'common/test/data/', ['simple'])
        ms = modulestore('direct')
        did_load_item = False
        try:       
            ms.get_item(Location(['i4x', 'edX', 'simple', 'problem', 'ps01-simple', None]))
            did_load_item = True
        except ItemNotFoundError:
            pass

        # make sure we found the item (e.g. it didn't error while loading)
        self.assertTrue(did_load_item)   

    def test_metadata_inheritance(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        ms = modulestore('direct')
        course = ms.get_item(Location(['i4x', 'edX', 'full', 'course', '6.002_Spring_2012', None]))

        verticals = ms.get_items(['i4x', 'edX', 'full', 'vertical', None, None])

        # let's assert on the metadata_inheritance on an existing vertical
        for vertical in verticals:
            self.assertIn('xqa_key', vertical.metadata)
            self.assertEqual(course.metadata['xqa_key'], vertical.metadata['xqa_key'])

        self.assertGreater(len(verticals), 0)

        new_component_location = Location('i4x', 'edX', 'full', 'html', 'new_component')
        source_template_location = Location('i4x', 'edx', 'templates', 'html', 'Blank_HTML_Page')
        
        # crate a new module and add it as a child to a vertical
        ms.clone_item(source_template_location, new_component_location)
        parent = verticals[0]
        ms.update_children(parent.location, parent.definition.get('children', []) + [new_component_location.url()])

        # flush the cache
        ms.get_cached_metadata_inheritance_tree(new_component_location, -1)
        new_module = ms.get_item(new_component_location)

        # check for grace period definition which should be defined at the course level
        self.assertIn('graceperiod', new_module.metadata)

        self.assertEqual(course.metadata['graceperiod'], new_module.metadata['graceperiod'])

        #
        # now let's define an override at the leaf node level
        #
        new_module.metadata['graceperiod'] = '1 day'
        ms.update_metadata(new_module.location, new_module.metadata)

        # flush the cache and refetch
        ms.get_cached_metadata_inheritance_tree(new_component_location, -1)
        new_module = ms.get_item(new_component_location)

        self.assertIn('graceperiod', new_module.metadata)
        self.assertEqual('1 day', new_module.metadata['graceperiod'])


class TemplateTestCase(ModuleStoreTestCase):

    def test_template_cleanup(self):        
        ms = modulestore('direct')

        # insert a bogus template in the store
        bogus_template_location = Location('i4x', 'edx', 'templates', 'html', 'bogus')
        source_template_location = Location('i4x', 'edx', 'templates', 'html', 'Blank_HTML_Page')
        
        ms.clone_item(source_template_location, bogus_template_location)

        verify_create = ms.get_item(bogus_template_location)
        self.assertIsNotNone(verify_create)

        # now run cleanup
        update_templates()

        # now try to find dangling template, it should not be in DB any longer
        asserted = False
        try:
            verify_create = ms.get_item(bogus_template_location)
        except ItemNotFoundError:
            asserted = True

        self.assertTrue(asserted)     


