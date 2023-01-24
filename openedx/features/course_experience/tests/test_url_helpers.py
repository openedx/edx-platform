"""
Test some of the functions in url_helpers
"""
from unittest import mock

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

from .. import url_helpers


def _patch_courseware_mfe_is_active(ret_val):
    return mock.patch.object(
        url_helpers,
        'courseware_mfe_is_active',
        return_value=ret_val,
    )


@ddt.ddt
class IsLearningMfeTests(TestCase):
    """
    Test is_request_from_learning_mfe.
    """

    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()

    @ddt.data(
        ('', '', False,),
        ('https://mfe-url/', 'https://platform-url/course', False,),
        ('https://mfe-url/', 'https://mfe-url/course', True,),
        ('https://mfe-url/', 'https://mfe-url/', True,),
        ('https://mfe-url/subpath/', 'https://platform-url/course', False,),
        ('https://mfe-url/subpath/', 'https://mfe-url/course', True,),
        ('https://mfe-url/subpath/', 'https://mfe-url/', True,),
    )
    @ddt.unpack
    def test_is_request_from_learning_mfe(self, mfe_url, referrer_url, is_mfe):
        with override_settings(LEARNING_MICROFRONTEND_URL=mfe_url):
            request = self.request_factory.get('/course')
            request.META['HTTP_REFERER'] = referrer_url
            assert url_helpers.is_request_from_learning_mfe(request) == is_mfe


@ddt.ddt
class GetCoursewareUrlTests(SharedModuleStoreTestCase):
    """
    Test get_courseware_url.

    Mock out `courseware_mfe_is_active`; that is tested elseware.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up data used across test functions.
        """
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.items = cls.create_test_courses()

    @classmethod
    def create_test_courses(cls):
        """
        We build simple course structures.
        Course structure is a non-branching tree from the root Course block down
        to the Component-level problem block;

        For easy access in the test functions, we return a dict like this:
        {
            "course_run": <course block for Split Mongo course>,
            "section": <chapter block in course run>
            "subsection": <sequence block in section>
            "unit": <vertical block in subsection>
            "component": <problem block in unit>
        }
        """

        course_run = CourseFactory.create(
            org='TestX',
            number='UrlHelpers',
            run='split',
            display_name='URL Helpers Test Course',
        )
        with cls.store.bulk_operations(course_run.id):
            section = BlockFactory.create(
                parent_location=course_run.location,
                category='chapter',
                display_name="Generated Section",
            )
            subsection = BlockFactory.create(
                parent_location=section.location,
                category='sequential',
                display_name="Generated Subsection",
            )
            unit = BlockFactory.create(
                parent_location=subsection.location,
                category='vertical',
                display_name="Generated Unit",
            )
            component = BlockFactory.create(
                parent_location=unit.location,
                category='problem',
                display_name="Generated Problem Component",
            )

        return {
            'course_run': course_run,
            'section': section,
            'subsection': subsection,
            'unit': unit,
            'component': component,
        }

    @ddt.data(
        (
            'mfe',
            'course_run',
            'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split'
        ),
        (
            'mfe',
            'section',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@chapter+block@Generated_Section'
            ),
        ),
        (
            'mfe',
            'subsection',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection'
            ),
        ),
        (
            'mfe',
            'unit',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection' +
                '/block-v1:TestX+UrlHelpers+split+type@vertical+block@Generated_Unit'
            ),
        ),
        (
            'mfe',
            'component',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection' +
                '/block-v1:TestX+UrlHelpers+split+type@vertical+block@Generated_Unit'
            ),
        ),
        (
            'legacy',
            'course_run',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware',
        ),
        (
            'legacy',
            'subsection',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/',
        ),
        (
            'legacy',
            'unit',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/1',
        ),
        (
            'legacy',
            'component',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/1',
        )
    )
    @ddt.unpack
    def test_get_courseware_url(
        self,
        active_experience,
        structure_level,
        expected_path,
    ):
        """
        Given:
        * a `store_type` ('split' or [old] 'mongo'),
        * an `active_experience` ('mfe' or 'legacy'),
        * and a `structure_level` ('course_run', 'section', 'subsection', 'unit', or 'component'),

        check that the expected path (URL without querystring) is returned by `get_courseware_url`.
        """
        block = self.items[structure_level]
        with _patch_courseware_mfe_is_active(active_experience == 'mfe') as mock_mfe_is_active:
            url = url_helpers.get_courseware_url(block.location)
        path = url.split('?')[0]
        assert path == expected_path
        course_run = self.items['course_run']
        mock_mfe_is_active.assert_called_once()
