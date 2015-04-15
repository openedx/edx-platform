"""
Tests for views/tools.py.
"""

import datetime
import mock
import json
import unittest

from django.utils.timezone import utc
from django.test.utils import override_settings

from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from student.tests.factories import UserFactory  # pylint: disable=import-error
from xmodule.fields import Date
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from opaque_keys.edx.keys import CourseKey

from ..views import tools

DATE_FIELD = Date()


class TestDashboardError(unittest.TestCase):
    """
    Test DashboardError exceptions.
    """
    def test_response(self):
        error = tools.DashboardError(u'Oh noes!')
        response = json.loads(error.response().content)
        self.assertEqual(response, {'error': 'Oh noes!'})


class TestHandleDashboardError(unittest.TestCase):
    """
    Test handle_dashboard_error decorator.
    """
    def test_error(self):
        # pylint: disable=unused-argument
        @tools.handle_dashboard_error
        def view(request, course_id):
            """
            Raises DashboardError.
            """
            raise tools.DashboardError("Oh noes!")

        response = json.loads(view(None, None).content)
        self.assertEqual(response, {'error': 'Oh noes!'})

    def test_no_error(self):
        # pylint: disable=unused-argument
        @tools.handle_dashboard_error
        def view(request, course_id):
            """
            Returns "Oh yes!"
            """
            return "Oh yes!"

        self.assertEqual(view(None, None), "Oh yes!")


class TestRequireStudentIdentifier(unittest.TestCase):
    """
    Test require_student_from_identifier()
    """
    def setUp(self):
        """
        Fixtures
        """
        super(TestRequireStudentIdentifier, self).setUp()
        self.student = UserFactory.create()

    def test_valid_student_id(self):
        self.assertEqual(
            self.student,
            tools.require_student_from_identifier(self.student.username)
        )

    def test_invalid_student_id(self):
        with self.assertRaises(tools.DashboardError):
            tools.require_student_from_identifier("invalid")


class TestParseDatetime(unittest.TestCase):
    """
    Test date parsing.
    """
    def test_parse_no_error(self):
        self.assertEqual(
            tools.parse_datetime('5/12/2010 2:42'),
            datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc))

    def test_parse_error(self):
        with self.assertRaises(tools.DashboardError):
            tools.parse_datetime('foo')


class TestFindUnit(ModuleStoreTestCase):
    """
    Test the find_unit function.
    """

    def setUp(self):
        """
        Fixtures.
        """
        super(TestFindUnit, self).setUp()

        course = CourseFactory.create()
        week1 = ItemFactory.create(parent=course)
        homework = ItemFactory.create(parent=week1)

        self.course = course
        self.homework = homework

    def test_find_unit_success(self):
        """
        Test finding a nested unit.
        """
        url = self.homework.location.to_deprecated_string()
        found_unit = tools.find_unit(self.course, url)
        self.assertEqual(found_unit.location, self.homework.location)

    def test_find_unit_notfound(self):
        """
        Test attempt to find a unit that does not exist.
        """
        url = "i4x://MITx/999/chapter/notfound"
        with self.assertRaises(tools.DashboardError):
            tools.find_unit(self.course, url)


class TestGetUnitsWithDueDate(ModuleStoreTestCase):
    """
    Test the get_units_with_due_date function.
    """
    def setUp(self):
        """
        Fixtures.
        """
        super(TestGetUnitsWithDueDate, self).setUp()

        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)
        course = CourseFactory.create()
        week1 = ItemFactory.create(due=due, parent=course)
        week2 = ItemFactory.create(due=due, parent=course)

        ItemFactory.create(
            parent=week1,
            due=due
        )

        self.course = course
        self.week1 = week1
        self.week2 = week2

    def test_it(self):

        def urls(seq):
            "URLs for sequence of nodes."
            return sorted(i.location.to_deprecated_string() for i in seq)

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
        unit.location.to_deprecated_string.return_value = 'test:hello'
        self.assertEquals(tools.title_or_url(unit), 'test:hello')


@override_settings(
    FIELD_OVERRIDE_PROVIDERS=(
        'courseware.student_field_overrides.IndividualStudentOverrideProvider',),
)
class TestSetDueDateExtension(ModuleStoreTestCase):
    """
    Test the set_due_date_extensions function.
    """
    def setUp(self):
        """
        Fixtures.
        """
        super(TestSetDueDateExtension, self).setUp()
        OverrideFieldData.provider_classes = None

        self.due = due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)
        course = CourseFactory.create()
        week1 = ItemFactory.create(due=due, parent=course)
        week2 = ItemFactory.create(due=due, parent=course)
        week3 = ItemFactory.create(parent=course)
        homework = ItemFactory.create(parent=week1)
        assignment = ItemFactory.create(parent=homework, due=due)

        user = UserFactory.create()

        self.course = course
        self.week1 = week1
        self.homework = homework
        self.assignment = assignment
        self.week2 = week2
        self.week3 = week3
        self.user = user

        # Apparently the test harness doesn't use LmsFieldStorage, and I'm not
        # sure if there's a way to poke the test harness to do so.  So, we'll
        # just inject the override field storage in this brute force manner.
        for block in (course, week1, week2, week3, homework, assignment):
            block._field_data = OverrideFieldData.wrap(  # pylint: disable=protected-access
                user, block._field_data)  # pylint: disable=protected-access

    def tearDown(self):
        super(TestSetDueDateExtension, self).tearDown()
        OverrideFieldData.provider_classes = None

    def _clear_field_data_cache(self):
        """
        Clear field data cache for xblocks under test. Normally this would be
        done by virtue of the fact that xblocks are reloaded on subsequent
        requests.
        """
        for block in (self.week1, self.week2, self.week3,
                      self.homework, self.assignment):
            block.fields['due']._del_cached_value(block)  # pylint: disable=protected-access

    def test_set_due_date_extension(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        tools.set_due_date_extension(self.course, self.week1, self.user, extended)
        self._clear_field_data_cache()
        self.assertEqual(self.week1.due, extended)
        self.assertEqual(self.homework.due, extended)
        self.assertEqual(self.assignment.due, extended)

    def test_set_due_date_extension_num_queries(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        with self.assertNumQueries(4):
            tools.set_due_date_extension(self.course, self.week1, self.user, extended)
            self._clear_field_data_cache()

    def test_set_due_date_extension_invalid_date(self):
        extended = datetime.datetime(2009, 1, 1, 0, 0, tzinfo=utc)
        with self.assertRaises(tools.DashboardError):
            tools.set_due_date_extension(self.course, self.week1, self.user, extended)

    def test_set_due_date_extension_no_date(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        with self.assertRaises(tools.DashboardError):
            tools.set_due_date_extension(self.course, self.week3, self.user, extended)

    def test_reset_due_date_extension(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        tools.set_due_date_extension(self.course, self.week1, self.user, extended)
        tools.set_due_date_extension(self.course, self.week1, self.user, None)
        self.assertEqual(self.week1.due, self.due)


class TestDataDumps(ModuleStoreTestCase):
    """
    Test data dumps for reporting.
    """

    def setUp(self):
        """
        Fixtures.
        """
        super(TestDataDumps, self).setUp()

        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)
        course = CourseFactory.create()
        week1 = ItemFactory.create(due=due, parent=course)
        week2 = ItemFactory.create(due=due, parent=course)

        homework = ItemFactory.create(
            parent=week1,
            due=due
        )

        user1 = UserFactory.create()
        user2 = UserFactory.create()
        self.course = course
        self.week1 = week1
        self.homework = homework
        self.week2 = week2
        self.user1 = user1
        self.user2 = user2

    def test_dump_module_extensions(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        tools.set_due_date_extension(self.course, self.week1, self.user1,
                                     extended)
        tools.set_due_date_extension(self.course, self.week1, self.user2,
                                     extended)
        report = tools.dump_module_extensions(self.course, self.week1)
        self.assertEqual(
            report['title'], u'Users with due date extensions for ' +
            self.week1.display_name)
        self.assertEqual(
            report['header'], ["Username", "Full Name", "Extended Due Date"])
        self.assertEqual(report['data'], [
            {"Username": self.user1.username,
             "Full Name": self.user1.profile.name,
             "Extended Due Date": "2013-12-25 00:00"},
            {"Username": self.user2.username,
             "Full Name": self.user2.profile.name,
             "Extended Due Date": "2013-12-25 00:00"}])

    def test_dump_student_extensions(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=utc)
        tools.set_due_date_extension(self.course, self.week1, self.user1,
                                     extended)
        tools.set_due_date_extension(self.course, self.week2, self.user1,
                                     extended)
        report = tools.dump_student_extensions(self.course, self.user1)
        self.assertEqual(
            report['title'], u'Due date extensions for %s (%s)' %
            (self.user1.profile.name, self.user1.username))
        self.assertEqual(
            report['header'], ["Unit", "Extended Due Date"])
        self.assertEqual(report['data'], [
            {"Unit": self.week1.display_name,
             "Extended Due Date": "2013-12-25 00:00"},
            {"Unit": self.week2.display_name,
             "Extended Due Date": "2013-12-25 00:00"}])


def msk_from_problem_urlname(course_id, urlname, block_type='problem'):
    """
    Convert a 'problem urlname' to a module state key (db field)
    """
    if not isinstance(course_id, CourseKey):
        raise ValueError
    if urlname.endswith(".xml"):
        urlname = urlname[:-4]

    return course_id.make_usage_key(block_type, urlname)
