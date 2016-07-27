"""
Course Structure api.py tests
"""
import mock
from django.core import cache

from .api import course_structure
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_structures.signals import listen_for_course_publish


class CourseStructureApiTests(ModuleStoreTestCase):
    """
    CourseStructure API Tests
    """
    MOCK_CACHE = "openedx.core.djangoapps.content.course_structures.api.v0.api.cache"

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        """
        Test setup
        """
        # For some reason, `listen_for_course_publish` is not called when we run
        # all (paver test_system -s cms) tests, If we run only run this file then tests run fine.
        SignalHandler.course_published.connect(listen_for_course_publish)

        super(CourseStructureApiTests, self).setUp()
        self.course = CourseFactory.create()
        self.chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Week 1"
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name="Lesson 1"
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 1'
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location, category="video", display_name="My Video"
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location, category="html", display_name="My HTML"
        )

        self.addCleanup(self._disconnect_course_published_event)

    def _disconnect_course_published_event(self):
        """
        Disconnect course_published event.
        """
        # If we don't disconnect then tests are getting failed in test_crud.py
        SignalHandler.course_published.disconnect(listen_for_course_publish)

    def _expected_blocks(self, block_types=None, get_parent=False):
        """
        Construct expected blocks.
        Arguments:
            block_types (list): List of required block types. Possible values include sequential,
                                vertical, html, problem, video, and discussion. The type can also be
                                the name of a custom type of block used for the course.
            get_parent (bool): If True then add child's parent location else parent is set to None
        Returns:
            dict: Information about required block types.
        """
        blocks = {}

        def add_block(xblock):
            """
            Returns expected blocks dict.
            """
            children = xblock.get_children()

            if block_types is None or xblock.category in block_types:

                parent = None
                if get_parent:
                    item = xblock.get_parent()
                    parent = unicode(item.location) if item is not None else None

                blocks[unicode(xblock.location)] = {
                    u'id': unicode(xblock.location),
                    u'type': xblock.category,
                    u'display_name': xblock.display_name,
                    u'format': xblock.format,
                    u'graded': xblock.graded,
                    u'parent': parent,
                    u'children': [unicode(child.location) for child in children]
                }

            for child in children:
                add_block(child)

        course = self.store.get_course(self.course.id, depth=None)
        add_block(course)

        return blocks

    def test_course_structure_with_no_block_types(self):
        """
        Verify that course_structure returns info for entire course.
        """
        with mock.patch(self.MOCK_CACHE, cache.caches['default']):
            with self.assertNumQueries(3):
                structure = course_structure(self.course.id)

        expected = {
            u'root': unicode(self.course.location),
            u'blocks': self._expected_blocks()
        }

        self.assertDictEqual(structure, expected)

        with mock.patch(self.MOCK_CACHE, cache.caches['default']):
            with self.assertNumQueries(2):
                course_structure(self.course.id)

    def test_course_structure_with_block_types(self):
        """
        Verify that course_structure returns info for required block_types only when specific block_types are requested.
        """
        block_types = ['html', 'video']

        with mock.patch(self.MOCK_CACHE, cache.caches['default']):
            with self.assertNumQueries(3):
                structure = course_structure(self.course.id, block_types=block_types)

        expected = {
            u'root': unicode(self.course.location),
            u'blocks': self._expected_blocks(block_types=block_types, get_parent=True)
        }

        self.assertDictEqual(structure, expected)

        with mock.patch(self.MOCK_CACHE, cache.caches['default']):
            with self.assertNumQueries(2):
                course_structure(self.course.id, block_types=block_types)

    def test_course_structure_with_non_existed_block_types(self):
        """
        Verify that course_structure returns empty info for non-existed block_types.
        """
        block_types = ['phantom']
        structure = course_structure(self.course.id, block_types=block_types)
        expected = {
            u'root': unicode(self.course.location),
            u'blocks': {}
        }

        self.assertDictEqual(structure, expected)
