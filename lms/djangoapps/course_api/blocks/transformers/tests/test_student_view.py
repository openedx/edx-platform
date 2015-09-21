from openedx.core.lib.block_cache.block_structure import BlockStructureFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from ..student_view import StudentViewTransformer


class TestStudentViewTransformer(ModuleStoreTestCase):

    def setUp(self):
        super(TestStudentViewTransformer, self).setUp()
        self.course_key = self.create_toy_course()
        self.course_root_loc = self.store.make_course_usage_key(self.course_key)
        self.block_structure = BlockStructureFactory.create_from_modulestore(
            self.course_root_loc, self.store
        )

    def test_collect(self):
        StudentViewTransformer.collect(self.block_structure)
