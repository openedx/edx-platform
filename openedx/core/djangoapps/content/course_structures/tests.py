import json

from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_structures.signals import listen_for_course_publish
from openedx.core.djangoapps.content.course_structures.tasks import _generate_course_structure, update_course_structure


class SignalDisconnectTestMixin(object):
    """
    Mixin for tests to disable calls to signals.listen_for_course_publish when the course_published signal is fired.
    """

    def setUp(self):
        super(SignalDisconnectTestMixin, self).setUp()
        SignalHandler.course_published.disconnect(listen_for_course_publish)


class CourseStructureTaskTests(ModuleStoreTestCase):
    def setUp(self, **kwargs):
        super(CourseStructureTaskTests, self).setUp()
        self.course = CourseFactory.create()
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        CourseStructure.objects.all().delete()

    def test_generate_course_structure(self):
        blocks = {}

        def add_block(block):
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
        self.assertDictEqual(actual, expected)

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
        actual = structure['blocks'][usage_key]
        expected = {
            "usage_key": usage_key,
            "block_type": category,
            "display_name": display_name,
            "graded": False,
            "format": None,
            "children": []
        }
        self.assertEqual(actual, expected)

    def test_update_course_structure(self):
        """
        Test the actual task that orchestrates data generation and updating the database.
        """
        # Method requires string input
        course_id = self.course.id
        self.assertRaises(ValueError, update_course_structure, course_id)

        # Ensure a CourseStructure object is created
        structure = _generate_course_structure(course_id)
        update_course_structure(unicode(course_id))
        cs = CourseStructure.objects.get(course_id=course_id)
        self.assertEqual(cs.course_id, course_id)
        self.assertEqual(cs.structure, structure)
