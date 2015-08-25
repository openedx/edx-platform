"""
Tests for the lms_result_processor
"""
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from courseware.tests.factories import UserFactory

from lms.lib.courseware_search.lms_result_processor import LmsSearchResultProcessor


class LmsSearchResultProcessorTestCase(ModuleStoreTestCase):
    """ Test case class to test search result processor """

    def build_course(self):
        """
        Build up a course tree with an html control
        """
        self.global_staff = UserFactory(is_staff=True)

        self.course = CourseFactory.create(
            org='Elasticsearch',
            course='ES101',
            run='test_run',
            display_name='Elasticsearch test course',
        )
        self.section = ItemFactory.create(
            parent=self.course,
            category='chapter',
            display_name='Test Section',
        )
        self.subsection = ItemFactory.create(
            parent=self.section,
            category='sequential',
            display_name='Test Subsection',
        )
        self.vertical = ItemFactory.create(
            parent=self.subsection,
            category='vertical',
            display_name='Test Unit',
        )
        self.html = ItemFactory.create(
            parent=self.vertical,
            category='html',
            display_name='Test Html control',
        )
        self.ghost_subsection = ItemFactory.create(
            parent=self.section,
            category='sequential',
            display_name=None,
        )
        self.ghost_vertical = ItemFactory.create(
            parent=self.ghost_subsection,
            category='vertical',
            display_name=None,
        )
        self.ghost_html = ItemFactory.create(
            parent=self.ghost_vertical,
            category='html',
            display_name='Ghost Html control',
        )

    def setUp(self):
        # from nose.tools import set_trace
        # set_trace()
        super(LmsSearchResultProcessorTestCase, self).setUp()
        self.build_course()

    def test_url_parameter(self):
        fake_url = ""
        srp = LmsSearchResultProcessor({}, "test")
        with self.assertRaises(ValueError):
            fake_url = srp.url
        self.assertEqual(fake_url, "")

        srp = LmsSearchResultProcessor(
            {
                "course": unicode(self.course.id),
                "id": unicode(self.html.scope_ids.usage_id),
                "content": {"text": "This is the html text"}
            },
            "test"
        )

        self.assertEqual(
            srp.url, "/courses/{}/jump_to/{}".format(unicode(self.course.id), unicode(self.html.scope_ids.usage_id)))

    def test_should_remove(self):
        """
        Tests that "visible_to_staff_only" overrides start date.
        """
        srp = LmsSearchResultProcessor(
            {
                "course": unicode(self.course.id),
                "id": unicode(self.html.scope_ids.usage_id),
                "content": {"text": "This is html test text"}
            },
            "test"
        )

        self.assertEqual(srp.should_remove(self.global_staff), False)
