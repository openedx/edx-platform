# coding=UTF-8
"""
tests for overrides
"""
import datetime
import mock
import pytz
from nose.plugins.attrib import attr

from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from django.test.utils import override_settings
from lms.djangoapps.courseware.tests.test_field_overrides import inject_field_overrides
from request_cache.middleware import RequestCache
from student.tests.factories import AdminFactory  # pylint: disable=import-error
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..models import CustomCourseForEdX
from ..overrides import override_field_for_ccx

from .test_views import flatten, iter_blocks


@attr('shard_1')
@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'ccx.overrides.CustomCoursesForEdxOverrideProvider',))
class TestFieldOverrides(ModuleStoreTestCase):
    """
    Make sure field overrides behave in the expected manner.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestFieldOverrides, self).setUp()
        self.course = course = CourseFactory.create()
        self.course.enable_ccx = True

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
        blocks = flatten([  # pylint: disable=unused-variable
            [ItemFactory.create(parent=vertical) for _ in xrange(2)]
            for vertical in verticals])

        self.ccx = ccx = CustomCourseForEdX(
            course_id=course.id,
            display_name='Test CCX',
            coach=AdminFactory.create())
        ccx.save()

        patch = mock.patch('ccx.overrides.get_current_ccx')
        self.get_ccx = get_ccx = patch.start()
        get_ccx.return_value = ccx
        self.addCleanup(patch.stop)

        self.addCleanup(RequestCache.clear_request_cache)

        inject_field_overrides(iter_blocks(ccx.course), course, AdminFactory.create())

        def cleanup_provider_classes():
            """
            After everything is done, clean up by un-doing the change to the
            OverrideFieldData object that is done during the wrap method.
            """
            OverrideFieldData.provider_classes = None
        self.addCleanup(cleanup_provider_classes)

    def test_override_start(self):
        """
        Test that overriding start date on a chapter works.
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)
        self.assertEquals(chapter.start, ccx_start)

    def test_override_num_queries_new_field(self):
        """
        Test that for creating new field executed only create query
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        with self.assertNumQueries(1):
            override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)

    def test_override_num_queries_update_existing_field(self):
        """
        Test that overriding existing field executed create, fetch and update queries.
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        new_ccx_start = datetime.datetime(2015, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)
        with self.assertNumQueries(2):
            override_field_for_ccx(self.ccx, chapter, 'start', new_ccx_start)

    def test_override_num_queries_field_value_not_changed(self):
        """
        Test that if value of field does not changed no query execute.
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)
        with self.assertNumQueries(0):
            override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)

    def test_overriden_field_access_produces_no_extra_queries(self):
        """
        Test no extra queries when accessing an overriden field more than once.
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        with self.assertNumQueries(1):
            override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)

    def test_override_is_inherited(self):
        """
        Test that sequentials inherit overridden start date from chapter.
        """
        ccx_start = datetime.datetime(2014, 12, 25, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        override_field_for_ccx(self.ccx, chapter, 'start', ccx_start)
        self.assertEquals(chapter.get_children()[0].start, ccx_start)
        self.assertEquals(chapter.get_children()[1].start, ccx_start)

    def test_override_is_inherited_even_if_set_in_mooc(self):
        """
        Test that a due date set on a chapter is inherited by grandchildren
        (verticals) even if a due date is set explicitly on grandchildren in
        the mooc.
        """
        ccx_due = datetime.datetime(2015, 1, 1, 00, 00, tzinfo=pytz.UTC)
        chapter = self.ccx.course.get_children()[0]
        chapter.display_name = 'itsme!'
        override_field_for_ccx(self.ccx, chapter, 'due', ccx_due)
        vertical = chapter.get_children()[0].get_children()[0]
        self.assertEqual(vertical.due, ccx_due)
