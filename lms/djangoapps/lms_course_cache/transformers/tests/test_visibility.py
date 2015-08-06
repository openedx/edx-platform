"""
Tests for VisibilityTransformation.
"""
import ddt

from courseware.access import has_access
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from lms_course_cache.api import get_course_blocks
from lms_course_cache.transformers.visibility import VisibilityTransformer


# TODO 8874: More comprehensively test VisibilityTransformation.

@ddt.ddt
class VisibilityTransformationTestCase(ModuleStoreTestCase):
    """
    ...
    """
    # TODO 8874: Change this VisibilityTransformationTestCase to use CourseStructureTestCase.

    # Tree formed by parent_map:
    #      0
    #     / \
    #    1   2
    #   / \
    #  3   4
    # Note the parents must always have lower indices than their children.
    parent_map = [None, 0, 0, 1, 1]

    @ddt.data({}, {0}, {1}, {2}, {2, 4}, {1, 2, 3, 4})
    def test_block_visibility(self, staff_only_blocks):

        course = CourseFactory.create(visible_to_staff_only=(0 in staff_only_blocks))
        course.save()
        xblocks = [course]

        for i, parent_index in enumerate(self.parent_map):
            if i == 0:
                continue
            xblocks.append(ItemFactory.create(
                parent=xblocks[parent_index],
                category="vertical",
                visible_to_staff_only=(i in staff_only_blocks),
            ))
        course.save()

        password = 'test'
        student = UserFactory.create(is_staff=False, password=password)
        staff = UserFactory.create(is_staff=True, password=password)
        CourseEnrollmentFactory.create(is_active=True, mode='honor', user=student, course_id=course.id)

        def check_against_has_access(user):
            self.client.login(username=user.username, password=password)
            block_structure = get_course_blocks(
                user, course.id, course.location, transformers=[VisibilityTransformer()]
            )
            for xblock in xblocks:
                self.assertEqual(
                    block_structure.has_block(xblock.location),
                    bool(has_access(user, 'load', xblock))
                )
            self.client.logout()

        check_against_has_access(student)
        check_against_has_access(staff)
