"""
Tests for the Badges app models.
"""


from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock, patch
from path import Path
from six.moves import range

from lms.djangoapps.badges.models import (
    BadgeAssertion,
    BadgeClass,
    CourseBadgesDisabledError,
    CourseCompleteImageConfiguration,
    validate_badge_image
)
from lms.djangoapps.badges.tests.factories import BadgeAssertionFactory, BadgeClassFactory, RandomBadgeClassFactory
from lms.djangoapps.certificates.tests.test_models import TEST_DATA_ROOT
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def get_image(name):
    """
    Get one of the test images from the test data directory.
    """
    return ImageFile(open(TEST_DATA_ROOT / 'badges' / name + '.png', mode='rb'))  # pylint: disable=open-builtin


@override_settings(MEDIA_ROOT=TEST_DATA_ROOT)
class BadgeImageConfigurationTest(TestCase):
    """
    Test the validation features of BadgeImageConfiguration.
    """

    def tearDown(self):
        tmp_path = Path(TEST_DATA_ROOT / 'course_complete_badges')
        Path.rmtree_p(tmp_path)

    def test_no_double_default(self):
        """
        Verify that creating two configurations as default is not permitted.
        """
        CourseCompleteImageConfiguration(mode='test', icon=get_image('good'), default=True).save()
        self.assertRaises(
            ValidationError,
            CourseCompleteImageConfiguration(mode='test2', icon=get_image('good'), default=True).full_clean
        )

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        self.assertRaises(
            ValidationError,
            CourseCompleteImageConfiguration(mode='test2', icon=get_image('unbalanced')).full_clean
        )


class DummyBackend(object):
    """
    Dummy badge backend, used for testing.
    """
    award = Mock()


@override_settings(MEDIA_ROOT=TEST_DATA_ROOT)
class BadgeClassTest(ModuleStoreTestCase):
    """
    Test BadgeClass functionality
    """

    def setUp(self):
        super(BadgeClassTest, self).setUp()
        self.addCleanup(self.cleanup_uploads)

    def cleanup_uploads(self):
        """
        Remove all files uploaded as badges.
        """
        upload_to = BadgeClass._meta.get_field('image').upload_to
        if default_storage.exists(upload_to):
            (_, files) = default_storage.listdir(upload_to)
            for uploaded_file in files:
                default_storage.delete(upload_to + '/' + uploaded_file)

    # Need full path to make sure class names line up.
    @override_settings(BADGING_BACKEND='lms.djangoapps.badges.tests.test_models.DummyBackend')
    def test_backend(self):
        """
        Verify the BadgeClass fetches the backend properly.
        """
        self.assertIsInstance(BadgeClass().backend, DummyBackend)

    def test_get_badge_class_preexisting(self):
        """
        Verify fetching a badge first grabs existing badges.
        """
        premade_badge_class = BadgeClassFactory.create()
        # Ignore additional parameters. This class already exists.
        badge_class = BadgeClass.get_badge_class(
            slug='test_slug', issuing_component='test_component', description='Attempted override',
            criteria='test', display_name='Testola', image_file_handle=get_image('good')
        )
        # These defaults are set on the factory.
        self.assertEqual(badge_class.criteria, 'https://example.com/syllabus')
        self.assertEqual(badge_class.display_name, 'Test Badge')
        self.assertEqual(badge_class.description, "Yay! It's a test badge.")
        # File name won't always be the same.
        self.assertEqual(badge_class.image.path, premade_badge_class.image.path)

    def test_unique_for_course(self):
        """
        Verify that the course_id is used in fetching existing badges or creating new ones.
        """
        course_key = CourseFactory.create().location.course_key
        premade_badge_class = BadgeClassFactory.create(course_id=course_key)
        badge_class = BadgeClass.get_badge_class(
            slug='test_slug', issuing_component='test_component', description='Attempted override',
            criteria='test', display_name='Testola', image_file_handle=get_image('good')
        )
        course_badge_class = BadgeClass.get_badge_class(
            slug='test_slug', issuing_component='test_component', description='Attempted override',
            criteria='test', display_name='Testola', image_file_handle=get_image('good'),
            course_id=course_key,
        )
        self.assertNotEqual(badge_class.id, course_badge_class.id)
        self.assertEqual(course_badge_class.id, premade_badge_class.id)

    def test_get_badge_class_course_disabled(self):
        """
        Verify attempting to fetch a badge class for a course which does not issue badges raises an
        exception.
        """
        course_key = CourseFactory.create(metadata={'issue_badges': False}).location.course_key
        with self.assertRaises(CourseBadgesDisabledError):
            BadgeClass.get_badge_class(
                slug='test_slug', issuing_component='test_component', description='Attempted override',
                criteria='test', display_name='Testola', image_file_handle=get_image('good'),
                course_id=course_key,
            )

    def test_get_badge_class_create(self):
        """
        Verify fetching a badge creates it if it doesn't yet exist.
        """
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description='This is a test',
            criteria='https://example.com/test_criteria', display_name='Super Badge',
            image_file_handle=get_image('good')
        )
        # This should have been saved before being passed back.
        self.assertTrue(badge_class.id)
        self.assertEqual(badge_class.slug, 'new_slug')
        self.assertEqual(badge_class.issuing_component, 'new_component')
        self.assertEqual(badge_class.description, 'This is a test')
        self.assertEqual(badge_class.criteria, 'https://example.com/test_criteria')
        self.assertEqual(badge_class.display_name, 'Super Badge')
        self.assertTrue('good' in badge_class.image.name.rsplit('/', 1)[-1])

    def test_get_badge_class_nocreate(self):
        """
        Test returns None if the badge class does not exist.
        """
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', create=False
        )
        self.assertIsNone(badge_class)
        # Run this twice to verify there wasn't a background creation of the badge.
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description=None,
            criteria=None, display_name=None,
            image_file_handle=None, create=False
        )
        self.assertIsNone(badge_class)

    def test_get_badge_class_image_validate(self):
        """
        Verify handing a broken image to get_badge_class raises a validation error upon creation.
        """
        self.assertRaises(
            ValidationError,
            BadgeClass.get_badge_class,
            slug='new_slug', issuing_component='new_component', description='This is a test',
            criteria='https://example.com/test_criteria', display_name='Super Badge',
            image_file_handle=get_image('unbalanced')
        )

    def test_get_badge_class_data_validate(self):
        """
        Verify handing incomplete data for required fields when making a badge class raises an Integrity error.
        """
        self.assertRaises(
            IntegrityError,
            BadgeClass.get_badge_class,
            slug='new_slug', issuing_component='new_component',
            image_file_handle=get_image('good')
        )

    def test_get_for_user(self):
        """
        Make sure we can get an assertion for a user if there is one.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        self.assertFalse(badge_class.get_for_user(user))
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=user)
        self.assertEqual(list(badge_class.get_for_user(user)), [assertion])

    @override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.badgr.BadgrBackend', BADGR_API_TOKEN='test')
    @patch('lms.djangoapps.badges.backends.badgr.BadgrBackend.award')
    def test_award(self, mock_award):
        """
        Verify that the award command calls the award function on the backend with the right parameters.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        badge_class.award(user, evidence_url='http://example.com/evidence')
        self.assertTrue(mock_award.called)
        mock_award.assert_called_with(badge_class, user, evidence_url='http://example.com/evidence')

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        self.assertRaises(
            ValidationError,
            BadgeClass(
                slug='test', issuing_component='test2', criteria='test3',
                description='test4', image=get_image('unbalanced')
            ).full_clean
        )


class BadgeAssertionTest(ModuleStoreTestCase):
    """
    Tests for the BadgeAssertion model
    """
    def test_assertions_for_user(self):
        """
        Verify that grabbing all assertions for a user behaves as expected.

        This function uses object IDs because for some reason Jenkins trips up
        on its assertCountEqual check here despite the items being equal.
        """
        user = UserFactory()
        assertions = [BadgeAssertionFactory.create(user=user).id for _i in range(3)]
        course = CourseFactory.create()
        course_key = course.location.course_key
        course_badges = [RandomBadgeClassFactory(course_id=course_key) for _i in range(3)]
        course_assertions = [
            BadgeAssertionFactory.create(user=user, badge_class=badge_class).id for badge_class in course_badges
        ]
        assertions.extend(course_assertions)
        assertions.sort()
        assertions_for_user = [badge.id for badge in BadgeAssertion.assertions_for_user(user)]
        assertions_for_user.sort()
        self.assertEqual(assertions_for_user, assertions)
        course_scoped_assertions = [
            badge.id for badge in BadgeAssertion.assertions_for_user(user, course_id=course_key)
        ]
        course_scoped_assertions.sort()
        self.assertEqual(course_scoped_assertions, course_assertions)


class ValidBadgeImageTest(TestCase):
    """
    Tests the badge image field validator.
    """
    def test_good_image(self):
        """
        Verify that saving a valid badge image is no problem.
        """
        validate_badge_image(get_image('good'))

    def test_unbalanced_image(self):
        """
        Verify that setting an image with an uneven width and height raises an error.
        """
        unbalanced = ImageFile(get_image('unbalanced'))
        self.assertRaises(ValidationError, validate_badge_image, unbalanced)

    def test_large_image(self):
        """
        Verify that setting an image that is too big raises an error.
        """
        large = get_image('large')
        self.assertRaises(ValidationError, validate_badge_image, large)
