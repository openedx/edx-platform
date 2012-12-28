import json
import shutil
from django.test import TestCase
from django.test.client import Client
from override_settings import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from path import path
from tempfile import mkdtemp
import json

from student.models import Registration
from django.contrib.auth.models import User
import xmodule.modulestore.django
from xmodule.modulestore.xml_importer import import_from_xml
import copy
from factories import *

from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.store_utilities import delete_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.xml_exporter import export_to_xml

def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)


def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)


class ContentStoreTestCase(TestCase):
    def _login(self, email, pw):
        """Login.  View should always return 200.  The success/fail is in the
        returned json"""
        resp = self.client.post(reverse('login_post'),
                                {'email': email, 'password': pw})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, pw):
        """Login, check that it worked."""
        resp = self._login(email, pw)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def _create_account(self, username, email, pw):
        """Try to create an account.  No error checking"""
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': pw,
            'location': 'home',
            'language': 'Franglish',
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, pw):
        """Create the account and check that it worked"""
        resp = self._create_account(username, email, pw)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(user(email).is_active)

        return resp

    def _activate_user(self, email):
        """Look up the activation key for the user, then hit the activate view.
        No error checking"""
        activation_key = registration(email).activation_key

        # and now we try to activate
        resp = self.client.get(reverse('activate', kwargs={'key': activation_key}))
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(user(email).is_active)


class AuthTestCase(ContentStoreTestCase):
    """Check that various permissions-related things work"""

    def setUp(self):
        self.email = 'a@b.com'
        self.pw = 'xyz'
        self.username = 'testuser'
        self.client = Client()

    def check_page_get(self, url, expected):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, expected)
        return resp

    def test_public_pages_load(self):
        """Make sure pages that don't require login load without error."""
        pages = (
                 reverse('login'),
                 reverse('signup'),
                 )
        for page in pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, 200)

    def test_create_account_errors(self):
        # No post data -- should fail
        resp = self.client.post('/create_account', {})
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], False)

    def test_create_account(self):
        self.create_account(self.username, self.email, self.pw)
        self.activate_user(self.email)

    def test_login(self):
        self.create_account(self.username, self.email, self.pw)

        # Not activated yet.  Login should fail.
        resp = self._login(self.email, self.pw)
        data = parse_json(resp)
        self.assertFalse(data['success'])

        self.activate_user(self.email)

        # Now login should work
        self.login(self.email, self.pw)

    def test_private_pages_auth(self):
        """Make sure pages that do require login work."""
        auth_pages = (
            reverse('index'),
            )

        # These are pages that should just load when the user is logged in
        # (no data needed)
        simple_auth_pages = (
            reverse('index'),
            )

        # need an activated user
        self.test_create_account()

        # Create a new session
        self.client = Client()

        # Not logged in.  Should redirect to login.
        print 'Not logged in'
        for page in auth_pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, expected=302)

        # Logged in should work.
        self.login(self.email, self.pw)

        print 'Logged in'
        for page in simple_auth_pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, expected=200)

    def test_index_auth(self):

        # not logged in.  Should return a redirect.
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 302)

        # Logged in should work.

TEST_DATA_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
TEST_DATA_MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
TEST_DATA_MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')

@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class ContentStoreTest(TestCase):

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

        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        xmodule.templates.update_templates()

        self.client = Client()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }

    def tearDown(self):
        # Make sure you flush out the test modulestore after the end
        # of the last test because otherwise on the next run
        # cms/djangoapps/contentstore/__init__.py
        # update_templates() will try to update the templates
        # via upsert and it sometimes seems to be messing things up.
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

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
            '<h1>My Courses</h1>',
            status_code=200,
            html=True)

    def test_course_factory(self):
        course = CourseFactory.create()
        self.assertIsInstance(course, xmodule.course_module.CourseDescriptor)

    def test_item_factory(self):
        course = CourseFactory.create()
        item = ItemFactory.create(parent_location=course.location)
        self.assertIsInstance(item, xmodule.seq_module.SequenceDescriptor)

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
            '<a href="/MITx/999/course/Robot_Super_Course" class="class-name">Robot Super Course</a>',
            status_code=200,
            html=True)

    def test_clone_item(self):
        """Test cloning an item. E.g. creating a new section"""
        CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        section_data = {
            'parent_location' : 'i4x://MITx/999/course/Robot_Super_Course',
            'template' : 'i4x://edx/templates/chapter/Empty',
            'display_name': 'Section One',
            }

        resp = self.client.post(reverse('clone_item'), section_data)

        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertRegexpMatches(data['id'], 
            '^i4x:\/\/MITx\/999\/chapter\/([0-9]|[a-f]){32}$')

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

    def test_clone_course(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        resp = self.client.post(reverse('create_new_course'), self.course_data)
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
        items = ms.get_items(Location(['i4x','edX', 'full', 'vertical', None]))
        self.assertGreater(len(items), 0)
        clone_items = ms.get_items(Location(['i4x', 'MITx','999','vertical', None]))
        self.assertGreater(len(clone_items), 0)
        for descriptor in items:
            new_loc = descriptor.location._replace(org = 'MITx', course='999')
            print "Checking {0} should now also be at {1}".format(descriptor.location.url(), new_loc.url())
            resp = self.client.get(reverse('edit_unit', kwargs={'location': new_loc.url()}))
            self.assertEqual(resp.status_code, 200)

    def test_delete_course(self):
        import_from_xml(modulestore(), 'common/test/data/', ['full'])

        ms = modulestore('direct')
        cs = contentstore()

        location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')

        delete_course(ms, cs, location)

        items = ms.get_items(Location(['i4x','edX', 'full', 'vertical', None]))
        self.assertEqual(len(items), 0)

    def test_export_course(self):
        ms = modulestore('direct')
        cs = contentstore() 

        import_from_xml(ms, 'common/test/data/', ['full'])
        location = CourseDescriptor.id_to_location('edX/full/6.002_Spring_2012')

        root_dir = path(mkdtemp())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(ms, cs, location, root_dir, 'test_export')

        # remove old course
        delete_course(ms, cs, location)

        # reimport
        import_from_xml(ms, root_dir, ['test_export'])

        items = ms.get_items(Location(['i4x','edX', 'full', 'vertical', None]))
        self.assertGreater(len(items), 0)
        for descriptor in items:
            print "Checking {0}....".format(descriptor.location.url())
            resp = self.client.get(reverse('edit_unit', kwargs={'location': descriptor.location.url()}))
            self.assertEqual(resp.status_code, 200)

        shutil.rmtree(root_dir)        

    def test_course_handouts_rewrites(self):
        ms = modulestore('direct')
        cs = contentstore() 

        import_from_xml(ms, 'common/test/data/', ['full'])     

        handout_location= Location(['i4x', 'edX', 'full', 'course_info', 'handouts'])

        resp = self.client.get(reverse('module_info', kwargs={'module_location': handout_location}))

        self.assertEqual(resp.status_code, 200)

        # check that /static/ has been converted to the full path
        # note, we know the link it should be because that's what in the 'full' course in the test data
        self.assertContains(resp, '/c4x/edX/full/asset/handouts_schematic_tutorial.pdf') 






        





