"""

"""

from django.core.management import call_command, CommandError

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class DeletionCommandTestCase(ModuleStoreTestCase):
    def test_cms_remove_stray_courses_command_no_courses(self):
        """
        Raise CommandError if there's no courses to delete.
        """
        with self.assertRaises(CommandError):
            call_command('cms_remove_stray_courses')

    def test_cms_remove_stray_courses_command(self):
        """
        Removes all courses that has only MongoDB entry.
        """
        CourseFactory.create()
        call_command('cms_remove_stray_courses')

    def test_cms_remove_stray_courses_command_non_to_delete(self):
        """
        Should not remove courses from MongoDB if it has a MySQL CourseOverview entry.
        """
        course = CourseFactory.create()
        CourseOverviewFactory.create(id=course.id)

        with self.assertRaises(CommandError):
            call_command('cms_remove_stray_courses')
