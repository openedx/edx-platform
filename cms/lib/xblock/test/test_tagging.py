"""
Tests for the Studio Tagging XBlockAside
"""

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xblock_config.models import StudioConfig
from cms.lib.xblock.tagging import StructuredTagsAside
from contentstore.views.preview import get_preview_fragment
from contentstore.utils import reverse_usage_url
from contentstore.tests.utils import AjaxEnabledTestClient
from django.test.client import RequestFactory
from student.tests.factories import UserFactory
from opaque_keys.edx.asides import AsideUsageKeyV1
from datetime import datetime
from pytz import UTC
from lxml import etree
from StringIO import StringIO


class StructuredTagsAsideTestCase(ModuleStoreTestCase):
    """
    Base class for tests of StructuredTagsAside (tagging.py)
    """
    def setUp(self):
        """
        Preparation for the test execution
        """
        self.user_password = super(StructuredTagsAsideTestCase, self).setUp()
        self.aside_name = 'tagging_aside'
        self.aside_tag = 'difficulty_tag'
        self.aside_tag_value = 'hard'

        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        self.course = ItemFactory.create(
            parent_location=course.location,
            category="course",
            display_name="Test course",
        )
        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
            start=datetime(2015, 3, 1, tzinfo=UTC),
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name="Lesson 1",
            publish_item=True,
            start=datetime(2015, 3, 1, tzinfo=UTC),
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location,
            category='vertical',
            display_name='Subsection 1',
            publish_item=True,
            start=datetime(2015, 4, 1, tzinfo=UTC),
        )
        self.problem = ItemFactory.create(
            category="problem",
            parent_location=self.vertical.location,
            display_name="A Problem Block",
            weight=1,
            user_id=self.user.id,
            publish_item=False,
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location,
            category='video',
            display_name='My Video',
            user_id=self.user.id
        )

        config = StudioConfig.current()
        config.enabled = True
        config.save()

    def test_aside_contains_tags(self):
        """
        Checks that available_tags list is not empty
        """
        self.assertGreater(len(StructuredTagsAside.available_tags), 0,
                           "StructuredTagsAside should contains at least one available tag")

    def test_preview_html(self):
        """
        Checks that html for the StructuredTagsAside is generated correctly
        """
        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        problem_html = get_preview_fragment(request, self.problem, context).content

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(problem_html), parser)

        main_div_nodes = tree.xpath('/html/body/div/section/div')
        self.assertEquals(len(main_div_nodes), 1)

        div_node = main_div_nodes[0]
        self.assertEquals(div_node.get('data-init'), 'StructuredTagsInit')
        self.assertEquals(div_node.get('data-runtime-class'), 'PreviewRuntime')
        self.assertEquals(div_node.get('data-block-type'), 'tagging_aside')
        self.assertEquals(div_node.get('data-runtime-version'), '1')
        self.assertIn('xblock_asides-v1', div_node.get('class'))

        select_nodes = div_node.xpath('div/select')
        self.assertEquals(len(select_nodes), 1)

        select_node = select_nodes[0]
        self.assertEquals(select_node.get('name'), self.aside_tag)

        # Now ensure the acid_aside is not in the result
        self.assertNotRegexpMatches(problem_html, r"data-block-type=[\"\']acid_aside[\"\']")

        # Ensure about video don't have asides
        video_html = get_preview_fragment(request, self.video, context).content
        self.assertNotRegexpMatches(video_html, "<select")

    def test_handle_requests(self):
        """
        Checks that handler to save tags in StructuredTagsAside works properly
        """
        handler_url = reverse_usage_url(
            'preview_handler',
            '%s:%s::%s' % (AsideUsageKeyV1.CANONICAL_NAMESPACE, self.problem.location, self.aside_name),
            kwargs={'handler': 'save_tags'}
        )

        client = AjaxEnabledTestClient()
        client.login(username=self.user.username, password=self.user_password)

        response = client.post(path=handler_url, data={})
        self.assertEqual(response.status_code, 400)

        response = client.post(path=handler_url, data={'tag': 'undefined_tag:undefined'})
        self.assertEqual(response.status_code, 400)

        val = '%s:undefined' % self.aside_tag
        response = client.post(path=handler_url, data={'tag': val})
        self.assertEqual(response.status_code, 400)

        val = '%s:%s' % (self.aside_tag, self.aside_tag_value)
        response = client.post(path=handler_url, data={'tag': val})
        self.assertEqual(response.status_code, 200)

        problem = modulestore().get_item(self.problem.location)
        asides = problem.runtime.get_asides(problem)
        tag_aside = None
        for aside in asides:
            if isinstance(aside, StructuredTagsAside):
                tag_aside = aside
                break

        self.assertIsNotNone(tag_aside, "Necessary StructuredTagsAside object isn't found")
        self.assertEqual(tag_aside.saved_tags[self.aside_tag], self.aside_tag_value)
