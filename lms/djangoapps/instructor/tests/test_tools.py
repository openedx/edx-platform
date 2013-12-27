"""
Tests for views/tools.py.
"""

import datetime
import mock
import json
import unittest

from django.utils.timezone import utc
from django.test.utils import override_settings

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..views import tools


class TestDashboardError(unittest.TestCase):
    """
    Test DashboardError exceptions.
    """
    def test_response(self):
        error = tools.DashboardError(u'Oh noes!')
        response = json.loads(error.response().content)
        self.assertEqual(response, {'error': 'Oh noes!'})


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestFindUnit(ModuleStoreTestCase):
    """
    Test the find_unit function.
    """

    def setUp(self):
        """
        Fixtures.
        """
        course = CourseFactory.create()
        week1 = ItemFactory.create()
        homework = ItemFactory.create(parent_location=week1.location)
        week1.children.append(homework.location)
        course.children.append(week1.location)

        self.course = course
        self.homework = homework

    def test_find_unit_success(self):
        """
        Test finding a nested unit.
        """
        url = self.homework.location.url()
        self.assertEqual(tools.find_unit(self.course, url), self.homework)

    def test_find_unit_notfound(self):
        """
        Test attempt to find a unit that does not exist.
        """
        url = "i4x://MITx/999/chapter/notfound"
        with self.assertRaises(tools.DashboardError):
            tools.find_unit(self.course, url)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestGetUnitsWithDueDate(ModuleStoreTestCase):
    """
    Test the get_units_with_due_date function.
    """
    def setUp(self):
        """
        Fixtures.
        """
        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)
        course = CourseFactory.create()
        week1 = ItemFactory.create(due=due)
        week2 = ItemFactory.create(due=due)
        course.children = [week1.location.url(), week2.location.url()]

        homework = ItemFactory.create(
            parent_location=week1.location,
            due=due
        )
        week1.children = [homework.location.url()]

        self.course = course
        self.week1 = week1
        self.week2 = week2

    def test_it(self):

        def urls(seq):
            "URLs for sequence of nodes."
            return sorted(i.location.url() for i in seq)

        self.assertEquals(
            urls(tools.get_units_with_due_date(self.course)),
            urls((self.week1, self.week2)))


class TestTitleOrUrl(unittest.TestCase):
    """
    Test the title_or_url funciton.
    """
    def test_title(self):
        unit = mock.Mock(display_name='hello')
        self.assertEquals(tools.title_or_url(unit), 'hello')

    def test_url(self):
        unit = mock.Mock(display_name=None)
        unit.location.url.return_value = 'test:hello'
        self.assertEquals(tools.title_or_url(unit), 'test:hello')


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestSetDueDateExtension(ModuleStoreTestCase):
    """
    Test the set_due_date_extensions function.
    """
    def setUp(self):
        """
        Fixtures.
        """
        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)
        course = CourseFactory.create()
        week1 = ItemFactory.create(due=due)
        week2 = ItemFactory.create(due=due)
        course.children = [week1.location.url(), week2.location.url()]

        homework = ItemFactory.create(
            parent_location=week1.location,
            due=due
        )
        week1.children = [homework.location.url()]

        user = UserFactory.create()

        self.course = course
        self.week1 = week1
        self.homeowrk = homework
        self.week2 = week2
        self.user = user

    def test_set_due_date_extension(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        tools.set_due_date_extension(self.course, self.week1, self.user,
                                     extended)
        import pdb; pdb.set_trace()
        self.assertEqual(self.week1.extended_due, extended)
        self.assertEqual(self.homework.extended_due, extended)
