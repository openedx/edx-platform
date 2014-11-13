import datetime
import mock
import pytz

from courseware.field_overrides import OverrideFieldData
from django.test.utils import override_settings
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..models import PersonalOnlineCourse
from ..overrides import override_field_for_poc


@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'pocs.overrides.PersonalOnlineCoursesOverrideProvider',))
class TestFieldOverrides(ModuleStoreTestCase):
    """
    Make sure field overrides behave in the expected manner.
    """
    def setUp(self):
        """
        Set up tests
        """
        self.course = course = CourseFactory.create()

        # Create a course outline
        self.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC)
        self.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC)
        chapters = [ItemFactory.create(start=start, parent=course)
                    for _ in xrange(2)]
        sequentials = flatten([
            [ItemFactory.create(parent=chapter) for _ in xrange(2)]
            for chapter in chapters])
        verticals = flatten([
            [ItemFactory.create(due=due, parent=sequential) for _ in xrange(2)]
            for sequential in sequentials])
        blocks = flatten([
            [ItemFactory.create(parent=vertical) for _ in xrange(2)]
            for vertical in verticals])

        self.poc = poc = PersonalOnlineCourse(
            course_id=course.id,
            display_name='Test POC',
            coach=AdminFactory.create())
        poc.save()

        patch = mock.patch('pocs.overrides.get_current_poc')
        self.get_poc = get_poc = patch.start()
        get_poc.return_value = poc
        self.addCleanup(patch.stop)

        # Apparently the test harness doesn't use LmsFieldStorage, and I'm not
        # sure if there's a way to poke the test harness to do so.  So, we'll
        # just inject the override field storage in this brute force manner.
        OverrideFieldData.provider_classes = None
        for block in iter_blocks(course):
            block._field_data = OverrideFieldData.wrap(  # pylint: disable=protected-access
                AdminFactory.create(), block._field_data)  # pylint: disable=protected-access

    def test_override_start(self):
        """
        Test that overriding start date on a chapter works.
        """
        poc_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.course.get_children()[0]
        override_field_for_poc(self.poc, chapter, 'start', poc_start)
        self.assertEquals(chapter.start, poc_start)

    def test_override_is_inherited(self):
        """
        Test that sequentials inherit overridden start date from chapter.
        """
        poc_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.course.get_children()[0]
        override_field_for_poc(self.poc, chapter, 'start', poc_start)
        self.assertEquals(chapter.get_children()[0].start, poc_start)
        self.assertEquals(chapter.get_children()[1].start, poc_start)

    def test_override_is_inherited_even_if_set_in_mooc(self):
        """
        Test that a due date set on a chapter is inherited by grandchildren
        (verticals) even if a due date is set explicitly on grandchildren in
        the mooc.
        """
        poc_due = datetime.datetime(2015, 1, 1, 00, 00, tzinfo=pytz.UTC)
        chapter = self.course.get_children()[0]
        chapter.display_name = 'itsme!'
        override_field_for_poc(self.poc, chapter, 'due', poc_due)
        vertical = chapter.get_children()[0].get_children()[0]
        self.assertEqual(vertical.due, poc_due)


def flatten(seq):
    """
    For [[1, 2], [3, 4]] returns [1, 2, 3, 4].  Does not recurse.
    """
    return [x for sub in seq for x in sub]


def iter_blocks(course):
    """
    Returns an iterator over all of the blocks in a course.
    """
    def visit(block):
        yield block
        for child in block.get_children():
            for descendant in visit(child):  # wish they'd backport yield from
                yield descendant
    return visit(course)
