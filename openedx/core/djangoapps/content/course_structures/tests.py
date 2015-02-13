import json
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_structures.models import generate_course_structure, CourseStructure


class CourseStructureTests(ModuleStoreTestCase):
    def setUp(self, **kwargs):
        super(CourseStructureTests, self).setUp()
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
        actual = generate_course_structure(self.course.id)
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
        cs = CourseStructure.objects.create(course_id=self.course.id, structure_json=structure_json)
        self.assertEqual(cs.structure_json, structure_json)

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
