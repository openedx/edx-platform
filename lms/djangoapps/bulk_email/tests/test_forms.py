"""
Unit tests for bulk-email-related forms.
"""
from django.test.utils import override_settings
from django.conf import settings

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import MONGO_MODULESTORE_TYPE

from mock import patch

from bulk_email.models import CourseAuthorization
from bulk_email.forms import CourseAuthorizationAdminForm


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class CourseAuthorizationFormTest(ModuleStoreTestCase):
    """Test the CourseAuthorizationAdminForm form for Mongo-backed courses."""

    def setUp(self):
        # Make a mongo course
        self.course = CourseFactory.create()

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_authorize_mongo_course(self):
        # Initially course shouldn't be authorized
        self.assertFalse(CourseAuthorization.instructor_email_enabled(self.course.id))
        # Test authorizing the course, which should totally work
        form_data = {'course_id': self.course.id, 'email_enabled': True}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation should work
        self.assertTrue(form.is_valid())
        form.save()
        # Check that this course is authorized
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_repeat_course(self):
        # Initially course shouldn't be authorized
        self.assertFalse(CourseAuthorization.instructor_email_enabled(self.course.id))
        # Test authorizing the course, which should totally work
        form_data = {'course_id': self.course.id, 'email_enabled': True}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation should work
        self.assertTrue(form.is_valid())
        form.save()
        # Check that this course is authorized
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))

        # Now make a new course authorization with the same course id that tries to turn email off
        form_data = {'course_id': self.course.id, 'email_enabled': False}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation should not work because course_id field is unique
        self.assertFalse(form.is_valid())
        self.assertEquals(
            "Course authorization with this Course id already exists.",
            form._errors['course_id'][0]  # pylint: disable=protected-access
        )
        with self.assertRaisesRegexp(ValueError, "The CourseAuthorization could not be created because the data didn't validate."):
            form.save()

        # Course should still be authorized (invalid attempt had no effect)
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_form_typo(self):
        # Munge course id
        bad_id = self.course.id + '_typo'

        form_data = {'course_id': bad_id, 'email_enabled': True}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation shouldn't work
        self.assertFalse(form.is_valid())

        msg = u'Error encountered (Course not found.)'
        msg += ' --- Entered course id was: "{0}". '.format(bad_id)
        msg += 'Please recheck that you have supplied a course id in the format: ORG/COURSE/RUN'
        self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The CourseAuthorization could not be created because the data didn't validate."):
            form.save()

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_course_name_only(self):
        # Munge course id - common
        bad_id = self.course.id.split('/')[-1]

        form_data = {'course_id': bad_id, 'email_enabled': True}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation shouldn't work
        self.assertFalse(form.is_valid())

        msg = u'Error encountered (Need more than 1 value to unpack)'
        msg += ' --- Entered course id was: "{0}". '.format(bad_id)
        msg += 'Please recheck that you have supplied a course id in the format: ORG/COURSE/RUN'
        self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The CourseAuthorization could not be created because the data didn't validate."):
            form.save()


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CourseAuthorizationXMLFormTest(ModuleStoreTestCase):
    """Check that XML courses cannot be authorized for email."""

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_xml_course_authorization(self):
        course_id = 'edX/toy/2012_Fall'
        # Assert this is an XML course
        self.assertTrue(modulestore().get_modulestore_type(course_id) != MONGO_MODULESTORE_TYPE)

        form_data = {'course_id': course_id, 'email_enabled': True}
        form = CourseAuthorizationAdminForm(data=form_data)
        # Validation shouldn't work
        self.assertFalse(form.is_valid())

        msg = u"Course Email feature is only available for courses authored in Studio. "
        msg += '"{0}" appears to be an XML backed course.'.format(course_id)
        self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access

        with self.assertRaisesRegexp(ValueError, "The CourseAuthorization could not be created because the data didn't validate."):
            form.save()
