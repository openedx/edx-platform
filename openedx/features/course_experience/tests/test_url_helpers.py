"""
Test some of the functions in url_helpers
"""
from unittest import mock

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

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
        We build two simple course structures (one using Split, the other Old Mongo).
        Each course structure is a non-branching tree from the root Course block down
        to the Component-level problem block; that is, we make one item for each course
        hierarchy level.

        For easy access in the test functions, we return them in a dict like this:
        {
            "split": {
                "course_run": <course block for Split Mongo course>,
                "section": <chapter block in course run>
                "subsection": <sequence block in section>
                "unit": <vertical block in subsection>
                "component": <problem block in unit>
            },
            "mongo": {
                "course_run": <course block for (deprecated) Old Mongo course>,
                ... etc ...
            }
        }
        """

        # Make Split Mongo course.
        with cls.store.default_store(ModuleStoreEnum.Type.split):
            course_run = CourseFactory.create(
                org='TestX',
                number='UrlHelpers',
                run='split',
                display_name='URL Helpers Test Course',
            )
            with cls.store.bulk_operations(course_run.id):
                section = ItemFactory.create(
                    parent_location=course_run.location,
                    category='chapter',
                    display_name="Generated Section",
                )
                subsection = ItemFactory.create(
                    parent_location=section.location,
                    category='sequential',
                    display_name="Generated Subsection",
                )
                unit = ItemFactory.create(
                    parent_location=subsection.location,
                    category='vertical',
                    display_name="Generated Unit",
                )
                component = ItemFactory.create(
                    parent_location=unit.location,
                    category='problem',
                    display_name="Generated Problem Component",
                )

        # Make (deprecated) Old Mongo course.
        with cls.store.default_store(ModuleStoreEnum.Type.mongo):
            deprecated_course_run = CourseFactory.create(
                org='TestX',
                number='UrlHelpers',
                run='mongo',
                display_name='URL Helpers Test Course (Deprecated)',
            )
            with cls.store.bulk_operations(deprecated_course_run.id):
                deprecated_section = ItemFactory.create(
                    parent_location=deprecated_course_run.location,
                    category='chapter',
                    display_name="Generated Section",
                )
                deprecated_subsection = ItemFactory.create(
                    parent_location=deprecated_section.location,
                    category='sequential',
                    display_name="Generated Subsection",
                )
                deprecated_unit = ItemFactory.create(
                    parent_location=deprecated_subsection.location,
                    category='vertical',
                    display_name="Generated Unit",
                )
                deprecated_component = ItemFactory.create(
                    parent_location=deprecated_unit.location,
                    category='problem',
                    display_name="Generated Problem Component",
                )

        return {
            ModuleStoreEnum.Type.split: {
                'course_run': course_run,
                'section': section,
                'subsection': subsection,
                'unit': unit,
                'component': component,
            },
            ModuleStoreEnum.Type.mongo: {
                'course_run': deprecated_course_run,
                'section': deprecated_section,
                'subsection': deprecated_subsection,
                'unit': deprecated_unit,
                'component': deprecated_component,
            }
        }

    @ddt.data(
        (
            ModuleStoreEnum.Type.split,
            'mfe',
            'course_run',
            'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split'
        ),
        (
            ModuleStoreEnum.Type.split,
            'mfe',
            'section',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@chapter+block@Generated_Section'
            ),
        ),
        (
            ModuleStoreEnum.Type.split,
            'mfe',
            'subsection',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection'
            ),
        ),
        (
            ModuleStoreEnum.Type.split,
            'mfe',
            'unit',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection' +
                '/block-v1:TestX+UrlHelpers+split+type@vertical+block@Generated_Unit'
            ),
        ),
        (
            ModuleStoreEnum.Type.split,
            'mfe',
            'component',
            (
                'http://learning-mfe/course/course-v1:TestX+UrlHelpers+split' +
                '/block-v1:TestX+UrlHelpers+split+type@sequential+block@Generated_Subsection' +
                '/block-v1:TestX+UrlHelpers+split+type@vertical+block@Generated_Unit'
            ),
        ),
        (
            ModuleStoreEnum.Type.split,
            'legacy',
            'course_run',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware',
        ),
        (
            ModuleStoreEnum.Type.split,
            'legacy',
            'subsection',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/',
        ),
        (
            ModuleStoreEnum.Type.split,
            'legacy',
            'unit',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/1',
        ),
        (
            ModuleStoreEnum.Type.split,
            'legacy',
            'component',
            '/courses/course-v1:TestX+UrlHelpers+split/courseware/Generated_Section/Generated_Subsection/1',
        ),
        (
            ModuleStoreEnum.Type.mongo,
            'legacy',
            'course_run',
            '/courses/TestX/UrlHelpers/mongo/courseware',
        ),
        (
            ModuleStoreEnum.Type.mongo,
            'legacy',
            'subsection',
            '/courses/TestX/UrlHelpers/mongo/courseware/Generated_Section/Generated_Subsection/',
        ),
        (
            ModuleStoreEnum.Type.mongo,
            'legacy',
            'unit',
            '/courses/TestX/UrlHelpers/mongo/courseware/Generated_Section/Generated_Subsection/1',
        ),
        (
            ModuleStoreEnum.Type.mongo,
            'legacy',
            'component',
            '/courses/TestX/UrlHelpers/mongo/courseware/Generated_Section/Generated_Subsection/1',
        ),
    )
    @ddt.unpack
    def test_get_courseware_url(
        self,
        store_type,
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
        block = self.items[store_type][structure_level]
        with _patch_courseware_mfe_is_active(active_experience == 'mfe') as mock_mfe_is_active:
            url = url_helpers.get_courseware_url(block.location)
        path = url.split('?')[0]
        assert path == expected_path
        course_run = self.items[store_type]['course_run']
        mock_mfe_is_active.assert_called_once()
