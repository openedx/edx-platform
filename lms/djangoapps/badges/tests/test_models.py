"""
Tests for the Badges app models.
"""


import contextlib
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings
from path import Path

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.badges.models import (
    BadgeAssertion,
    BadgeClass,
    CourseBadgesDisabledError,
    CourseCompleteImageConfiguration,
    validate_badge_image
)
from lms.djangoapps.badges.tests.factories import BadgeAssertionFactory, BadgeClassFactory, RandomBadgeClassFactory
from lms.djangoapps.certificates.tests.test_models import TEST_DATA_ROOT, TEST_DATA_DIR
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


@contextlib.contextmanager
def get_image(name):
    """
    Get one of the test images from the test data directory.
    """
    with open(f'{TEST_DATA_DIR}/badges/{name}.png', mode='rb') as fimage:
        yield ImageFile(fimage)


@override_settings(MEDIA_ROOT=TEST_DATA_ROOT)
class BadgeImageConfigurationTest(TestCase):
    """
    Test the validation features of BadgeImageConfiguration.
    """

    def tearDown(self):  # lint-amnesty, pylint: disable=super-method-not-called
        tmp_path = Path(TEST_DATA_ROOT / 'course_complete_badges')
        Path.rmtree_p(tmp_path)

    def test_no_double_default(self):
        """
        Verify that creating two configurations as default is not permitted.
        """
        with get_image('good') as image_handle:
            CourseCompleteImageConfiguration(mode='test', icon=ImageFile(image_handle), default=True).save()
        with get_image('good') as image_handle:
            pytest.raises(ValidationError, CourseCompleteImageConfiguration(mode='test2', icon=ImageFile(image_handle),
                                                                            default=True).full_clean)

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        with get_image('unbalanced') as image_handle:
            pytest.raises(
                ValidationError,
                CourseCompleteImageConfiguration(mode='test2', icon=ImageFile(image_handle)).full_clean
            )


class DummyBackend:
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
        super().setUp()
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
        assert isinstance(BadgeClass().backend, DummyBackend)

    def test_get_badge_class_preexisting(self):
        """
        Verify fetching a badge first grabs existing badges.
        """
        premade_badge_class = BadgeClassFactory.create()
        # Ignore additional parameters. This class already exists.
        with get_image('good') as image_handle:
            badge_class = BadgeClass.get_badge_class(
                slug='test_slug', issuing_component='test_component', description='Attempted override',
                criteria='test', display_name='Testola', image_file_handle=image_handle
            )
        # These defaults are set on the factory.
        assert badge_class.criteria == 'https://example.com/syllabus'
        assert badge_class.display_name == 'Test Badge'
        assert badge_class.description == "Yay! It's a test badge."
        # File name won't always be the same.
        assert badge_class.image.path == premade_badge_class.image.path

    def test_unique_for_course(self):
        """
        Verify that the course_id is used in fetching existing badges or creating new ones.
        """
        course_key = CourseFactory.create().location.course_key
        premade_badge_class = BadgeClassFactory.create(course_id=course_key)
        with get_image('good') as image_handle:
            badge_class = BadgeClass.get_badge_class(
                slug='test_slug', issuing_component='test_component', description='Attempted override',
                criteria='test', display_name='Testola', image_file_handle=image_handle
            )
        with get_image('good') as image_handle:
            course_badge_class = BadgeClass.get_badge_class(
                slug='test_slug', issuing_component='test_component', description='Attempted override',
                criteria='test', display_name='Testola', image_file_handle=image_handle,
                course_id=course_key,
            )
        assert badge_class.id != course_badge_class.id
        assert course_badge_class.id == premade_badge_class.id

    def test_get_badge_class_course_disabled(self):
        """
        Verify attempting to fetch a badge class for a course which does not issue badges raises an
        exception.
        """
        course_key = CourseFactory.create(metadata={'issue_badges': False}).location.course_key
        with pytest.raises(CourseBadgesDisabledError):
            with get_image('good') as image_handle:
                BadgeClass.get_badge_class(
                    slug='test_slug', issuing_component='test_component', description='Attempted override',
                    criteria='test', display_name='Testola', image_file_handle=image_handle,
                    course_id=course_key,
                )

    def test_get_badge_class_create(self):
        """
        Verify fetching a badge creates it if it doesn't yet exist.
        """
        with get_image('good') as image_handle:
            badge_class = BadgeClass.get_badge_class(
                slug='new_slug', issuing_component='new_component', description='This is a test',
                criteria='https://example.com/test_criteria', display_name='Super Badge',
                image_file_handle=image_handle
            )
        # This should have been saved before being passed back.
        assert badge_class.id
        assert badge_class.slug == 'new_slug'
        assert badge_class.issuing_component == 'new_component'
        assert badge_class.description == 'This is a test'
        assert badge_class.criteria == 'https://example.com/test_criteria'
        assert badge_class.display_name == 'Super Badge'
        assert 'good' in badge_class.image.name.rsplit('/', 1)[(- 1)]

    def test_get_badge_class_nocreate(self):
        """
        Test returns None if the badge class does not exist.
        """
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', create=False
        )
        assert badge_class is None
        # Run this twice to verify there wasn't a background creation of the badge.
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description=None,
            criteria=None, display_name=None,
            image_file_handle=None, create=False
        )
        assert badge_class is None

    def test_get_badge_class_image_validate(self):
        """
        Verify handing a broken image to get_badge_class raises a validation error upon creation.
        """
        # TODO Test should be updated, this doc doesn't makes sense, the object eventually gets created
        with get_image('unbalanced') as image_handle:
            self.assertRaises(
                ValidationError,
                BadgeClass.get_badge_class,
                slug='new_slug', issuing_component='new_component', description='This is a test',
                criteria='https://example.com/test_criteria', display_name='Super Badge',
                image_file_handle=image_handle
            )

    def test_get_badge_class_data_validate(self):
        """
        Verify handing incomplete data for required fields when making a badge class raises an Integrity error.
        """
        with pytest.raises(IntegrityError), self.allow_transaction_exception():
            with get_image('good') as image_handle:
                BadgeClass.get_badge_class(
                    slug='new_slug', issuing_component='new_component', image_file_handle=image_handle
                )

    def test_get_for_user(self):
        """
        Make sure we can get an assertion for a user if there is one.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        assert not badge_class.get_for_user(user)
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=user)
        assert list(badge_class.get_for_user(user)) == [assertion]

    @override_settings(
        BADGING_BACKEND='lms.djangoapps.badges.backends.badgr.BadgrBackend',
        BADGR_USERNAME='example@example.com',
        BADGR_PASSWORD='password',
        BADGR_TOKENS_CACHE_KEY='badgr-test-cache-key')
    @patch('lms.djangoapps.badges.backends.badgr.BadgrBackend.award')
    def test_award(self, mock_award):
        """
        Verify that the award command calls the award function on the backend with the right parameters.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        badge_class.award(user, evidence_url='http://example.com/evidence')
        assert mock_award.called
        mock_award.assert_called_with(badge_class, user, evidence_url='http://example.com/evidence')

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        with get_image('unbalanced') as image_handle:
            pytest.raises(
                ValidationError,
                BadgeClass(
                    slug='test', issuing_component='test2', criteria='test3',
                    description='test4', image=ImageFile(image_handle)).full_clean
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
        assert assertions_for_user == assertions
        course_scoped_assertions = [
            badge.id for badge in BadgeAssertion.assertions_for_user(user, course_id=course_key)
        ]
        course_scoped_assertions.sort()
        assert course_scoped_assertions == course_assertions


class ValidBadgeImageTest(TestCase):
    """
    Tests the badge image field validator.
    """
    def test_good_image(self):
        """
        Verify that saving a valid badge image is no problem.
        """
        with get_image('good') as image_handle:
            validate_badge_image(ImageFile(image_handle))

    def test_unbalanced_image(self):
        """
        Verify that setting an image with an uneven width and height raises an error.
        """
        with get_image('unbalanced') as image_handle:
            self.assertRaises(ValidationError, validate_badge_image, ImageFile(image_handle))

    def test_large_image(self):
        """
        Verify that setting an image that is too big raises an error.
        """
        with get_image('large') as image_handle:
            self.assertRaises(ValidationError, validate_badge_image, ImageFile(image_handle))
