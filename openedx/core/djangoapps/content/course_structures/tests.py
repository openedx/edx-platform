"""
Course Structure Content sub-application test cases
"""
import json
from nose.plugins.attrib import attr

from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_structures.signals import listen_for_course_publish
from openedx.core.djangoapps.content.course_structures.tasks import _generate_course_structure, update_course_structure
from openedx.core.djangoapps.xmodule_django.models import UsageKey


class SignalDisconnectTestMixin(object):
    """
    Mixin for tests to disable calls to signals.listen_for_course_publish when the course_published signal is fired.
    """

    def setUp(self):
        super(SignalDisconnectTestMixin, self).setUp()
        SignalHandler.course_published.disconnect(listen_for_course_publish)


@attr(shard=2)
class CourseStructureTaskTests(ModuleStoreTestCase):
    """
    Test cases covering Course Structure task-related workflows
    """
    def setUp(self, **kwargs):
        super(CourseStructureTaskTests, self).setUp()
        self.course = CourseFactory.create(org='TestX', course='TS101', run='T1')
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.discussion_xblock_1 = ItemFactory.create(
            parent=self.course,
            category='discussion',
            discussion_id='test_discussion_id_1'
        )
        self.discussion_xblock_2 = ItemFactory.create(
            parent=self.course,
            category='discussion',
            discussion_id='test_discussion_id_2'
        )
        CourseStructure.objects.all().delete()

    def test_generate_course_structure(self):
        blocks = {}

        def add_block(block):
            """
            Inserts new child XBlocks into the existing course tree
            """
            children = block.get_children() if block.has_children else []

            blocks[unicode(block.location)] = {
                "usage_key": unicode(block.location),
                "block_type": block.category,
                "display_name": block.display_name,
                "graded": block.graded,
                "format": block.format,
                "children": [unicode(child.location) for child in children]
            }

            for child in children:
                add_block(child)

        add_block(self.course)

        expected = {
            'root': unicode(self.course.location),
            'blocks': blocks
        }

        self.maxDiff = None
        actual = _generate_course_structure(self.course.id)
        self.assertDictEqual(actual['structure'], expected)

    def test_structure_json(self):
        """
        Although stored as compressed data, CourseStructure.structure_json should always return the uncompressed string.
        """
        course_id = 'a/b/c'
        structure = {
            'root': course_id,
            'blocks': {
                course_id: {
                    'id': course_id
                }
            }
        }
        structure_json = json.dumps(structure)
        structure = CourseStructure.objects.create(course_id=self.course.id, structure_json=structure_json)
        self.assertEqual(structure.structure_json, structure_json)

        # Reload the data to ensure the init signal is fired to decompress the data.
        cs = CourseStructure.objects.get(course_id=self.course.id)
        self.assertEqual(cs.structure_json, structure_json)

    def test_structure(self):
        """
        CourseStructure.structure should return the uncompressed, JSON-parsed course structure.
        """
        structure = {
            'root': 'a/b/c',
            'blocks': {
                'a/b/c': {
                    'id': 'a/b/c'
                }
            }
        }
        structure_json = json.dumps(structure)
        cs = CourseStructure.objects.create(course_id=self.course.id, structure_json=structure_json)
        self.assertDictEqual(cs.structure, structure)

    def test_ordered_blocks(self):
        structure = {
            'root': 'a/b/c',
            'blocks': {
                'a/b/c': {
                    'id': 'a/b/c',
                    'children': [
                        'g/h/i'
                    ]
                },
                'd/e/f': {
                    'id': 'd/e/f',
                    'children': []
                },
                'g/h/i': {
                    'id': 'h/j/k',
                    'children': [
                        'j/k/l',
                        'd/e/f'
                    ]
                },
                'j/k/l': {
                    'id': 'j/k/l',
                    'children': []
                }
            }
        }
        in_order_blocks = ['a/b/c', 'g/h/i', 'j/k/l', 'd/e/f']
        structure_json = json.dumps(structure)
        retrieved_course_structure = CourseStructure.objects.create(
            course_id=self.course.id, structure_json=structure_json
        )

        self.assertEqual(retrieved_course_structure.ordered_blocks.keys(), in_order_blocks)

    def test_block_with_missing_fields(self):
        """
        The generator should continue to operate on blocks/XModule that do not have graded or format fields.
        """
        # TODO In the future, test logging using testfixtures.LogCapture
        # (https://pythonhosted.org/testfixtures/logging.html). Talk to TestEng before adding that library.
        category = 'peergrading'
        display_name = 'Testing Module'
        module = ItemFactory.create(parent=self.section, category=category, display_name=display_name)
        structure = _generate_course_structure(self.course.id)

        usage_key = unicode(module.location)
        actual = structure['structure']['blocks'][usage_key]
        expected = {
            "usage_key": usage_key,
            "block_type": category,
            "display_name": display_name,
            "graded": False,
            "format": None,
            "children": []
        }
        self.assertEqual(actual, expected)

    def test_generate_discussion_id_map(self):
        id_map = {}

        def add_block(block):
            """Adds the given block and all of its children to the expected discussion id map"""
            children = block.get_children() if block.has_children else []

            if block.category == 'discussion':
                id_map[block.discussion_id] = unicode(block.location)

            for child in children:
                add_block(child)

        add_block(self.course)

        actual = _generate_course_structure(self.course.id)
        self.assertEqual(actual['discussion_id_map'], id_map)

    def test_discussion_id_map_json(self):
        id_map = {
            'discussion_id_1': 'module_location_1',
            'discussion_id_2': 'module_location_2'
        }
        id_map_json = json.dumps(id_map)
        structure = CourseStructure.objects.create(course_id=self.course.id, discussion_id_map_json=id_map_json)
        self.assertEqual(structure.discussion_id_map_json, id_map_json)

        structure = CourseStructure.objects.get(course_id=self.course.id)
        self.assertEqual(structure.discussion_id_map_json, id_map_json)

    def test_discussion_id_map(self):
        id_map = {
            'discussion_id_1': 'block-v1:TestX+TS101+T1+type@discussion+block@b141953dff414921a715da37eb14ecdc',
            'discussion_id_2': 'i4x://TestX/TS101/discussion/466f474fa4d045a8b7bde1b911e095ca'
        }
        id_map_json = json.dumps(id_map)
        structure = CourseStructure.objects.create(course_id=self.course.id, discussion_id_map_json=id_map_json)
        expected_id_map = {
            key: UsageKey.from_string(value).map_into_course(self.course.id)
            for key, value in id_map.iteritems()
        }
        self.assertEqual(structure.discussion_id_map, expected_id_map)

    def test_discussion_id_map_missing(self):
        structure = CourseStructure.objects.create(course_id=self.course.id)
        self.assertIsNone(structure.discussion_id_map)

    def test_update_course_structure(self):
        """
        Test the actual task that orchestrates data generation and updating the database.
        """
        # Method requires string input
        course_id = self.course.id
        self.assertRaises(ValueError, update_course_structure, course_id)

        # Ensure a CourseStructure object is created
        expected_structure = _generate_course_structure(course_id)
        update_course_structure(unicode(course_id))
        structure = CourseStructure.objects.get(course_id=course_id)
        self.assertEqual(structure.course_id, course_id)
        self.assertEqual(structure.structure, expected_structure['structure'])
        self.assertEqual(structure.discussion_id_map.keys(), expected_structure['discussion_id_map'].keys())
        self.assertEqual(
            [unicode(value) for value in structure.discussion_id_map.values()],
            expected_structure['discussion_id_map'].values()
        )
