"""
Tests for the maintenance app views.
"""
import ddt
import itertools

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.roles import GlobalStaff
from student.tests.factories import AdminFactory, UserFactory

from contentstore.management.commands.utils import get_course_versions

from .views import COURSE_KEY_ERROR_MESSAGES, get_maintenace_urls


class CourseKeyMixin(object):

	def verify_error_message(self, data, error_msg):
		response = self.client.post(self.view_url, data=data)
		self.assertContains(response, error_msg, status_code=200)

	def verify_invalid_course_key(self, course_key, error_msg):
		self.verify_error_message({'course-id': course_key}, error_msg)

	def verify_bad_course_keys(self):
		self.verify_invalid_course_key('', COURSE_KEY_ERROR_MESSAGES['empty_course_key'])
		self.verify_invalid_course_key('edx', COURSE_KEY_ERROR_MESSAGES['invalid_course_key'])
		self.verify_invalid_course_key('course-v1:e+d+X', COURSE_KEY_ERROR_MESSAGES['course_key_not_found'])

	def validate_success_from_response(self, response, success_message):
		self.assertNotContains(response, '<div class="error">', status_code=200)
		self.assertContains(response, success_message, status_code=200)


class MaintenanceViewTestCase(ModuleStoreTestCase):
	"""
	Base class for maintenance view tests.
	"""

	def setUp(self):
		"""Create a user and log in. """
		super(MaintenanceViewTestCase, self).setUp()
		self.user = AdminFactory()
		success = self.client.login(username=self.user.username, password='test')
		self.assertTrue(success)
		self.course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)

	def tearDown(self):
		"""
		Reverse the setup
		"""
		self.client.logout()
		ModuleStoreTestCase.tearDown(self)	


@ddt.ddt
class MaintenanceViewAccessTests(MaintenanceViewTestCase):
	"""
	Tests for access control of maintenance views.
	"""

	@ddt.data(*(
		(url_name, role, has_access)
		for (url_name, (role, has_access))
		in itertools.product((
			"maintenance:maintenance",
			"maintenance:force_publish_course",
			"maintenance:show_orphans"
		), (
			(GlobalStaff, True),
			(None, False)
		))
	))
	@ddt.unpack
	def test_access(self, url_name, role, has_access):
		user = UserFactory(username='test', email="test@example.com", password="test")
		success = self.client.login(username=user.username, password='test')
		self.assertTrue(success)

		if role is not None:
			role().add_users(user)

		url = reverse(url_name)
		response = self.client.get(url)

		if has_access:
			self.assertEqual(response.status_code, 200)
		else:
			self.assertContains(response, _('Must be edX staff to perform this action.'), status_code=403)

	@ddt.data(
		"maintenance:maintenance",
		"maintenance:force_publish_course",
		"maintenance:show_orphans"
	)
	def test_require_login(self, url_name):
		url = reverse(url_name)

		# Log out then try to retrieve the page
		self.client.logout()
		response = self.client.get(url)

		# Expect a redirect to the login page
		redirect_url = "{login_url}?next={original_url}".format(
			login_url=reverse("login"),
			original_url=url,
		)

		self.assertRedirects(response, redirect_url)


class TestMaintenanceIndex(MaintenanceViewTestCase):
	"""
	Tests for maintenance index view.
	"""

	def setUp(self):
		"""Make the user global staff. """
		super(TestMaintenanceIndex, self).setUp()
		self.view_url = reverse('maintenance:maintenance')

	def test_maintenance_index(self):
		response = self.client.get(self.view_url)
		self.assertContains(response, "Maintenance", status_code=200)
		
		# Check that all the expected links appear on the index page.
		for url in get_maintenace_urls():
			self.assertContains(response, url, status_code=200)


@ddt.ddt
class TestForcePublish(MaintenanceViewTestCase, CourseKeyMixin):
	"""
	Tests for the force publish view.
	"""
	def setUp(self):
		super(TestForcePublish, self).setUp()
		self.view_url = reverse('maintenance:force_publish_course')
		# Add some changes to course
		chapter = ItemFactory.create(category='chapter', parent_location=self.course.location)
		self.store.create_child(
			self.user.id,
			chapter.location,
			'html',
			block_id='html_component'
		)
		# verify that course has changes.
		self.assertTrue(self.store.has_changes(self.store.get_item(self.course.location))) 
		   

	def test_validate_error_messages(self):
		"""
		Test all error messages for ForcePulish view.
		"""
		# validate all course key error messags
		self.verify_bad_course_keys()

		# validate non split error message
		course = CourseFactory.create(default_store=ModuleStoreEnum.Type.mongo)
		self.verify_error_message(
			{
				'course-id': unicode(course.id)
			},
			_('Force publish course does not support old mongo style courses.')
		)

		# Validate course already published 
		response = self.force_publish_course()
		self.validate_success_from_response(response, _('Now published and draft branch have same version'))

		# now course is forcefully published, we should get already published course.
		self.verify_error_message(
			{
				'course-id': unicode(self.course.id),
				'dry-run': False
			},
			_('Course is already in published state.')
		)

	def force_publish_course(self, is_dry_run=''):
		"""
		Force publish the course.
		"""
		# get draft and publish branch versions
		versions = get_course_versions(unicode(self.course.id))

		# verify that draft and publish point to different versions
		self.assertNotEqual(versions['draft-branch'], versions['published-branch'])

		# force publish course
		data = {
			'course-id': unicode(self.course.id),
			'dry-run': is_dry_run
		}
		return self.client.post(self.view_url, data=data)

	def test_force_publish_dry_run(self):
		"""
		Test complete flow of force publish as dry run.
		"""
		response = self.force_publish_course(is_dry_run='on')
		self.validate_success_from_response(response, _('Following course versions would be changed'))

		# verify that course still has changes as we just dry ran force publish course.
		self.assertTrue(self.store.has_changes(self.store.get_item(self.course.location)))

	def test_force_publish(self):
		"""
		Test complete flow of force publish.
		"""
		versions = get_course_versions(unicode(self.course.id))

		response = self.force_publish_course()
		self.validate_success_from_response(response, _('Now published and draft branch have same version'))

		# verify that course has no changes
		self.assertFalse(self.store.has_changes(self.store.get_item(self.course.location)))

		# get new draft and publish branch versions
		updated_versions = get_course_versions(unicode(self.course.id))

		# verify that the draft branch didn't change while the published branch did
		self.assertEqual(versions['draft-branch'], updated_versions['draft-branch'])
		self.assertNotEqual(versions['published-branch'], updated_versions['published-branch'])

		# verify that draft and publish point to same versions now
		self.assertEqual(updated_versions['draft-branch'], updated_versions['published-branch'])
