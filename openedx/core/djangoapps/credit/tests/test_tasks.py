"""
Tests for credit course tasks.
"""

import mock
from nose.plugins.attrib import attr
from datetime import datetime, timedelta

from pytz import UTC
from openedx.core.djangoapps.credit.api import get_credit_requirements
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.signals import on_course_publish
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls_range

from edx_proctoring.api import create_exam


@attr(shard=2)
class TestTaskExecution(ModuleStoreTestCase):
    """Set of tests to ensure that the task code will do the right thing when
    executed directly.

    The test course gets created without the listeners being present, which
    allows us to ensure that when the listener is executed, it is done as
    expected.
    """

    def mocked_set_credit_requirements(course_key, requirements):  # pylint: disable=no-self-argument, unused-argument
        """Used as a side effect when mocking method credit api method
        'set_credit_requirements'.
        """
        raise InvalidCreditRequirements

    def add_icrv_xblock(self, related_assessment_name=None, start_date=None):
        """ Create the 'edx-reverification-block' in course tree """
        block = ItemFactory.create(
            parent=self.vertical,
            category='edx-reverification-block',
        )

        if related_assessment_name is not None:
            block.related_assessment = related_assessment_name

        block.start = start_date

        self.store.update_item(block, ModuleStoreEnum.UserID.test)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.publish(block.location, ModuleStoreEnum.UserID.test)

        return block

    def setUp(self):
        super(TestTaskExecution, self).setUp()

        self.course = CourseFactory.create(start=datetime(2015, 3, 1))
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.subsection = ItemFactory.create(parent=self.section, category='sequential', display_name='Test Subsection')
        self.vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='Test Unit')

    def test_task_adding_requirements_invalid_course(self):
        """
        Test that credit requirements cannot be added for non credit course.
        """
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)

    def test_task_adding_requirements(self):
        """Test that credit requirements are added properly for credit course.

        Make sure that the receiver correctly fires off the task when
        invoked by signal.
        """
        self.add_credit_course(self.course.id)
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 1)

    def test_task_adding_icrv_requirements(self):
        """Make sure that the receiver correctly fires off the task when
        invoked by signal.
        """
        self.add_credit_course(self.course.id)
        self.add_icrv_xblock()
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 2)

    def test_proctored_exam_requirements(self):
        """
        Make sure that proctored exams are being registered as requirements
        """

        self.add_credit_course(self.course.id)

        create_exam(
            course_id=unicode(self.course.id),
            content_id=unicode(self.subsection.location),
            exam_name='A Proctored Exam',
            time_limit_mins=10,
            is_proctored=True,
            is_active=True
        )

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)

        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[1]['namespace'], 'proctored_exam')
        self.assertEqual(requirements[1]['name'], unicode(self.subsection.location))
        self.assertEqual(requirements[1]['display_name'], 'A Proctored Exam')
        self.assertEqual(requirements[1]['criteria'], {})

    def test_proctored_exam_filtering(self):
        """
        Make sure that timed or inactive exams do not end up in the requirements table
        Also practice protored exams are not a requirement
        """

        self.add_credit_course(self.course.id)
        create_exam(
            course_id=unicode(self.course.id),
            content_id='foo',
            exam_name='A Proctored Exam',
            time_limit_mins=10,
            is_proctored=False,
            is_active=True
        )

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)

        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 1)

        # make sure we don't have a proctoring requirement
        self.assertFalse([
            requirement
            for requirement in requirements
            if requirement['namespace'] == 'proctored_exam'
        ])

        create_exam(
            course_id=unicode(self.course.id),
            content_id='foo2',
            exam_name='A Proctored Exam',
            time_limit_mins=10,
            is_proctored=True,
            is_active=False
        )

        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 1)

        # make sure we don't have a proctoring requirement
        self.assertFalse([
            requirement
            for requirement in requirements
            if requirement['namespace'] == 'proctored_exam'
        ])

        # practice proctored exams aren't requirements
        create_exam(
            course_id=unicode(self.course.id),
            content_id='foo3',
            exam_name='A Proctored Exam',
            time_limit_mins=10,
            is_proctored=True,
            is_active=True,
            is_practice_exam=True
        )

        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 1)

        # make sure we don't have a proctoring requirement
        self.assertFalse([
            requirement
            for requirement in requirements
            if requirement['namespace'] == 'proctored_exam'
        ])

    def test_query_counts(self):
        self.add_credit_course(self.course.id)
        self.add_icrv_xblock()

        with check_mongo_calls_range(max_finds=11):
            on_course_publish(self.course.id)

    def test_remove_icrv_requirement(self):
        self.add_credit_course(self.course.id)
        self.add_icrv_xblock()
        on_course_publish(self.course.id)

        # There should be one ICRV requirement
        requirements = get_credit_requirements(self.course.id, namespace="reverification")
        self.assertEqual(len(requirements), 1)

        # Delete the parent section containing the ICRV block
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(self.subsection.location, ModuleStoreEnum.UserID.test)

        # Check that the ICRV block is no longer visible in the requirements
        on_course_publish(self.course.id)
        requirements = get_credit_requirements(self.course.id, namespace="reverification")
        self.assertEqual(len(requirements), 0)

    def test_icrv_requirement_ordering(self):
        self.add_credit_course(self.course.id)

        # Create multiple ICRV blocks
        start = datetime.now(UTC)
        self.add_icrv_xblock(related_assessment_name="Midterm A", start_date=start)

        start = start - timedelta(days=1)
        self.add_icrv_xblock(related_assessment_name="Midterm B", start_date=start)

        # Primary sort is based on start date
        on_course_publish(self.course.id)
        requirements = get_credit_requirements(self.course.id, namespace="reverification")
        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[0]["display_name"], "Midterm B")
        self.assertEqual(requirements[1]["display_name"], "Midterm A")

        # Add two additional ICRV blocks that have no start date
        # and the same name.
        start = datetime.now(UTC)
        first_block = self.add_icrv_xblock(related_assessment_name="Midterm Start Date")

        start = start + timedelta(days=1)
        second_block = self.add_icrv_xblock(related_assessment_name="Midterm Start Date")

        on_course_publish(self.course.id)
        requirements = get_credit_requirements(self.course.id, namespace="reverification")
        self.assertEqual(len(requirements), 4)
        # Since we are now primarily sorting on start_date and display_name if
        # start_date is present otherwise we are just sorting on display_name.
        self.assertEqual(requirements[0]["display_name"], "Midterm B")
        self.assertEqual(requirements[1]["display_name"], "Midterm A")
        self.assertEqual(requirements[2]["display_name"], "Midterm Start Date")
        self.assertEqual(requirements[3]["display_name"], "Midterm Start Date")

        # Since the last two requirements have the same display name,
        # we need to also check that their internal names (locations) are the same.
        self.assertEqual(requirements[2]["name"], first_block.get_credit_requirement_name())
        self.assertEqual(requirements[3]["name"], second_block.get_credit_requirement_name())

    @mock.patch(
        'openedx.core.djangoapps.credit.tasks.set_credit_requirements',
        mock.Mock(
            side_effect=mocked_set_credit_requirements
        )
    )
    def test_retry(self):
        """Test that adding credit requirements is retried when
        'InvalidCreditRequirements' exception is raised.

        Make sure that the receiver correctly fires off the task when
        invoked by signal
        """
        self.add_credit_course(self.course.id)
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)

    def test_credit_requirement_blocks_ordering(self):
        """
        Test ordering of the proctoring and ICRV blocks are in proper order.
        """

        self.add_credit_course(self.course.id)
        subsection = ItemFactory.create(parent=self.section, category='sequential', display_name='Dummy Subsection')
        create_exam(
            course_id=unicode(self.course.id),
            content_id=unicode(subsection.location),
            exam_name='A Proctored Exam',
            time_limit_mins=10,
            is_proctored=True,
            is_active=True
        )

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        on_course_publish(self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[1]['namespace'], 'proctored_exam')
        self.assertEqual(requirements[1]['name'], unicode(subsection.location))
        self.assertEqual(requirements[1]['display_name'], 'A Proctored Exam')
        self.assertEqual(requirements[1]['criteria'], {})

        # Create multiple ICRV blocks
        start = datetime.now(UTC)
        self.add_icrv_xblock(related_assessment_name="Midterm A", start_date=start)

        start = start - timedelta(days=1)
        self.add_icrv_xblock(related_assessment_name="Midterm B", start_date=start)

        # Primary sort is based on start date
        on_course_publish(self.course.id)
        requirements = get_credit_requirements(self.course.id)
        # grade requirement is added on publish of the requirements
        self.assertEqual(len(requirements), 4)
        # check requirements are added in the desired order
        # 1st Minimum grade then the blocks with start date than other blocks
        self.assertEqual(requirements[0]["display_name"], "Minimum Grade")
        self.assertEqual(requirements[1]["display_name"], "A Proctored Exam")
        self.assertEqual(requirements[2]["display_name"], "Midterm B")
        self.assertEqual(requirements[3]["display_name"], "Midterm A")

    def add_credit_course(self, course_key):
        """Add the course as a credit.

        Args:
            course_key(CourseKey): Identifier for the course

        Returns:
            CreditCourse object added
        """
        credit_course = CreditCourse(course_key=course_key, enabled=True)
        credit_course.save()
        return credit_course
