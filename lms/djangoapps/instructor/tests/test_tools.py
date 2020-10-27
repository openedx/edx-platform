"""
Tests for views/tools.py.
"""

import datetime
import json
import unittest

import mock
import six
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.test import TestCase
from django.test.utils import override_settings
from pytz import UTC
from opaque_keys.edx.keys import CourseKey
from six import text_type

from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from lms.djangoapps.ccx.tests.test_overrides import inject_field_overrides
from openedx.core.lib.tests import attr
from student.tests.factories import UserFactory
from xmodule.fields import Date
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..views import tools

DATE_FIELD = Date()


@attr(shard=1)
class TestDashboardError(unittest.TestCase):
    """
    Test DashboardError exceptions.
    """
    def test_response(self):
        error = tools.DashboardError(u'Oh noes!')
        response = json.loads(error.response().content)
        self.assertEqual(response, {'error': 'Oh noes!'})


@attr(shard=1)
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


@attr(shard=1)
class TestRequireStudentIdentifier(TestCase):
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


@attr(shard=1)
class TestParseDatetime(unittest.TestCase):
    """
    Test date parsing.
    """
    def test_parse_no_error(self):
        self.assertEqual(
            tools.parse_datetime('5/12/2010 2:42'),
            datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC))

    def test_parse_error(self):
        with self.assertRaises(tools.DashboardError):
            tools.parse_datetime('foo')


@attr(shard=1)
class TestFindUnit(SharedModuleStoreTestCase):
    """
    Test the find_unit function.
    """
    @classmethod
    def setUpClass(cls):
        super(TestFindUnit, cls).setUpClass()
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            week1 = ItemFactory.create(parent=cls.course)
            cls.homework = ItemFactory.create(parent=week1)

    def test_find_unit_success(self):
        """
        Test finding a nested unit.
        """
        url = text_type(self.homework.location)
        found_unit = tools.find_unit(self.course, url)
        self.assertEqual(found_unit.location, self.homework.location)

    def test_find_unit_notfound(self):
        """
        Test attempt to find a unit that does not exist.
        """
        url = "i4x://MITx/999/chapter/notfound"
        with self.assertRaises(tools.DashboardError):
            tools.find_unit(self.course, url)


@attr(shard=1)
class TestGetUnitsWithDueDate(ModuleStoreTestCase):
    """
    Test the get_units_with_due_date function.
    """
    def setUp(self):
        """
        Fixtures.
        """
        super(TestGetUnitsWithDueDate, self).setUp()

        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC)
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
            """
            URLs for sequence of nodes.
            """
            return sorted(text_type(i.location) for i in seq)

        self.assertEquals(
            urls(tools.get_units_with_due_date(self.course)),
            urls((self.week1, self.week2)))


@attr(shard=1)
class TestTitleOrUrl(unittest.TestCase):
    """
    Test the title_or_url funciton.
    """
    def test_title(self):
        unit = mock.Mock(display_name='hello')
        self.assertEquals(tools.title_or_url(unit), 'hello')

    def test_url(self):
        def mock_location_text(self):
            """
            Mock implementation of __unicode__ or __str__ for the unit's location.
            """
            return u'test:hello'

        unit = mock.Mock(display_name=None)
        if six.PY2:
            unit.location.__unicode__ = mock_location_text
        else:
            unit.location.__str__ = mock_location_text
        self.assertEquals(tools.title_or_url(unit), u'test:hello')


@attr(shard=1)
@override_settings(
    FIELD_OVERRIDE_PROVIDERS=(
        'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider',),
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

        self.due = due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC)
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

        inject_field_overrides((course, week1, week2, week3, homework, assignment), course, user)

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
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
        tools.set_due_date_extension(self.course, self.week1, self.user, extended)
        self._clear_field_data_cache()
        self.assertEqual(self.week1.due, extended)
        self.assertEqual(self.homework.due, extended)
        self.assertEqual(self.assignment.due, extended)

    def test_set_due_date_extension_num_queries(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
        with self.assertNumQueries(5):
            tools.set_due_date_extension(self.course, self.week1, self.user, extended)
            self._clear_field_data_cache()

    def test_set_due_date_extension_invalid_date(self):
        extended = datetime.datetime(2009, 1, 1, 0, 0, tzinfo=UTC)
        with self.assertRaises(tools.DashboardError):
            tools.set_due_date_extension(self.course, self.week1, self.user, extended)

    def test_set_due_date_extension_no_date(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
        with self.assertRaises(tools.DashboardError):
            tools.set_due_date_extension(self.course, self.week3, self.user, extended)

    def test_reset_due_date_extension(self):
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
        tools.set_due_date_extension(self.course, self.week1, self.user, extended)
        tools.set_due_date_extension(self.course, self.week1, self.user, None)
        self.assertEqual(self.week1.due, self.due)


@attr(shard=1)
class TestDataDumps(ModuleStoreTestCase):
    """
    Test data dumps for reporting.
    """

    def setUp(self):
        """
        Fixtures.
        """
        super(TestDataDumps, self).setUp()

        due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC)
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
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
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
        extended = datetime.datetime(2013, 12, 25, 0, 0, tzinfo=UTC)
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


@attr(shard=1)
class TestStudentFromIdentifier(TestCase):
    """
    Test get_student_from_identifier()
    """
    @classmethod
    def setUpClass(cls):
        super(TestStudentFromIdentifier, cls).setUpClass()
        cls.valid_student = UserFactory.create(username='baz@touchstone')
        cls.student_conflicting_email = UserFactory.create(email='foo@touchstone.com')
        cls.student_conflicting_username = UserFactory.create(username='foo@touchstone.com')

    def test_valid_student_id(self):
        """Test with valid username"""
        assert self.valid_student == tools.get_student_from_identifier(self.valid_student.username)

    def test_valid_student_email(self):
        """Test with valid email"""
        assert self.valid_student == tools.get_student_from_identifier(self.valid_student.email)

    def test_student_username_has_conflict_with_others_email(self):
        """
        An edge case where there is a user A with username example: foo@touchstone.com and
        there is user B with email example: foo@touchstone.com
        """
        with self.assertRaises(MultipleObjectsReturned):
            tools.get_student_from_identifier(self.student_conflicting_username.username)

        # can get student with alternative identifier, in this case email.
        assert self.student_conflicting_username == tools.get_student_from_identifier(
            self.student_conflicting_username.email
        )

    def test_student_email_has_conflict_with_others_username(self):
        """
        An edge case where there is a user A with email example: foo@touchstone.com and
        there is user B with username example: foo@touchstone.com
        """
        with self.assertRaises(MultipleObjectsReturned):
            tools.get_student_from_identifier(self.student_conflicting_email.email)

        # can get student with alternative identifier, in this case username.
        assert self.student_conflicting_email == tools.get_student_from_identifier(
            self.student_conflicting_email.username
        )

    def test_invalid_student_id(self):
        """Test with invalid identifier"""
        with self.assertRaises(User.DoesNotExist):
            assert tools.get_student_from_identifier("invalid")
