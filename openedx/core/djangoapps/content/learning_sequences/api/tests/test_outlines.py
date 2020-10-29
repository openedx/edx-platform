"""
Top level API tests. Tests API public contracts only. Do not import/create/mock
models for this app.
"""
from datetime import datetime, timezone

import attr
from django.contrib.auth.models import AnonymousUser, User
from edx_when.api import set_dates_for_course
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator

from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.tests.factories import BetaTesterFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG
from common.djangoapps.student.auth import user_has_role
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseBetaTesterRole

from ...data import CourseLearningSequenceData, CourseOutlineData, CourseSectionData, CourseVisibility, VisibilityData
from ..outlines import (
    get_course_outline,
    get_user_course_outline,
    get_user_course_outline_details,
    replace_course_outline
)
from .test_data import generate_sections


class CourseOutlineTestCase(CacheIsolationTestCase):
    """
    Simple tests around reading and writing CourseOutlineData. No user info.
    """
    @classmethod
    def setUpTestData(cls):
        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Learn+Roundtrip")
        normal_visibility = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=False
        )
        cls.course_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="Roundtrip Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2015",
            days_early_for_beta=None,
            sections=generate_sections(cls.course_key, [2, 2]),
            self_paced=False,
            course_visibility=CourseVisibility.PRIVATE
        )

    def test_deprecated_course_key(self):
        """Don't allow Old Mongo Courses at all."""
        old_course_key = CourseKey.from_string("Org/Course/Run")
        with self.assertRaises(ValueError):
            outline = get_course_outline(old_course_key)

    def test_simple_roundtrip(self):
        """Happy path for writing/reading-back a course outline."""
        with self.assertRaises(CourseOutlineData.DoesNotExist):
            course_outline = get_course_outline(self.course_key)

        replace_course_outline(self.course_outline)
        outline = get_course_outline(self.course_key)
        assert outline == self.course_outline

    def test_empty_course(self):
        """Empty Courses are a common case (when authoring just starts)."""
        empty_outline = attr.evolve(self.course_outline, sections=[])
        self.assertFalse(empty_outline.sections)
        self.assertFalse(empty_outline.sequences)
        replace_course_outline(empty_outline)
        assert empty_outline == get_course_outline(self.course_key)

    def test_empty_sections(self):
        """Empty Sections aren't very useful, but they shouldn't break."""
        empty_section_outline = attr.evolve(
            self.course_outline, sections=generate_sections(self.course_key, [0])
        )
        replace_course_outline(empty_section_outline)
        assert empty_section_outline == get_course_outline(self.course_key)

    def test_cached_response(self):
        # First lets seed the data...
        replace_course_outline(self.course_outline)

        # Uncached access always makes three database checks: LearningContext,
        # CourseSection, and CourseSectionSequence.
        with self.assertNumQueries(3):
            uncached_outline = get_course_outline(self.course_key)
            assert uncached_outline == self.course_outline

        # Successful cache access only makes a query to LearningContext to check
        # the current published version. That way we know that values are never
        # stale.
        with self.assertNumQueries(1):
            cached_outline = get_course_outline(self.course_key)

        # Cache hits in the same process are literally the same object.
        assert cached_outline is uncached_outline

        # Now we put a new version into the cache...
        new_version_outline = attr.evolve(
            self.course_outline, published_version="2222222222222222"
        )
        replace_course_outline(new_version_outline)

        # Make sure this new outline is returned instead of the previously
        # cached one.
        with self.assertNumQueries(3):
            uncached_new_version_outline = get_course_outline(self.course_key)
            assert new_version_outline == new_version_outline


class UserCourseOutlineTestCase(CacheIsolationTestCase):
    """
    Tests for basic UserCourseOutline functionality.
    """

    @classmethod
    def setUpTestData(cls):
        course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )
        cls.beta_tester = BetaTesterFactory(course_key=course_key)
        cls.anonymous_user = AnonymousUser()

        # Seed with data
        cls.course_key = course_key
        cls.simple_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            days_early_for_beta=None,
            sections=generate_sections(cls.course_key, [2, 1, 3]),
            self_paced=False,
            course_visibility=CourseVisibility.PRIVATE
        )
        replace_course_outline(cls.simple_outline)

        # Enroll student in the course
        CourseEnrollment.enroll(user=cls.student, course_key=cls.course_key, mode="audit")
        # Enroll beta tester in the course
        CourseEnrollment.enroll(user=cls.beta_tester, course_key=cls.course_key, mode="audit")

    def test_simple_outline(self):
        """This outline is the same for everyone."""
        at_time = datetime(2020, 5, 21, tzinfo=timezone.utc)
        beta_tester_outline = get_user_course_outline(
            self.course_key, self.beta_tester, at_time
        )
        student_outline = get_user_course_outline(
            self.course_key, self.student, at_time
        )
        global_staff_outline = get_user_course_outline(
            self.course_key, self.global_staff, at_time
        )
        assert beta_tester_outline.sections == global_staff_outline.sections
        assert student_outline.sections == global_staff_outline.sections
        assert student_outline.at_time == at_time

        beta_tester_outline_details = get_user_course_outline_details(
            self.course_key, self.beta_tester, at_time
        )
        assert beta_tester_outline_details.outline == beta_tester_outline

        student_outline_details = get_user_course_outline_details(
            self.course_key, self.student, at_time
        )
        assert student_outline_details.outline == student_outline

        global_staff_outline_details = get_user_course_outline_details(
            self.course_key, self.global_staff, at_time
        )
        assert global_staff_outline_details.outline == global_staff_outline


class ScheduleTestCase(CacheIsolationTestCase):
    """
    Schedule-specific Outline tests.

    These aren't super-comprehensive with edge cases yet, partly because it's
    still lacking a few important features (e.g. early beta releases, close-
    after-due policy, etc.), and I'm not sure how we want to structure the
    testing after all that's rolled up.
    """

    @classmethod
    def setUpTestData(cls):
        course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )
        cls.beta_tester = BetaTesterFactory(course_key=course_key)
        cls.anonymous_user = AnonymousUser()

        cls.course_key = course_key

        # The UsageKeys we're going to set up for date tests.
        cls.section_key = cls.course_key.make_usage_key('chapter', 'ch1')
        cls.seq_before_key = cls.course_key.make_usage_key('sequential', 'seq_before')
        cls.seq_same_key = cls.course_key.make_usage_key('sequential', 'seq_same')
        cls.seq_after_key = cls.course_key.make_usage_key('sequential', 'seq_after')
        cls.seq_inherit_key = cls.course_key.make_usage_key('sequential', 'seq_inherit')
        cls.seq_due_key = cls.course_key.make_usage_key('sequential', 'seq_due')

        cls.all_seq_keys = [
            cls.seq_before_key,
            cls.seq_same_key,
            cls.seq_after_key,
            cls.seq_inherit_key,
            cls.seq_due_key,
        ]

        # Set scheduling information into edx-when for a single Section with
        # sequences starting at various times.
        set_dates_for_course(
            cls.course_key,
            [
                (
                    cls.course_key.make_usage_key('course', 'course'),
                    {'start': datetime(2020, 5, 10, tzinfo=timezone.utc)}
                ),
                (
                    cls.section_key,
                    {'start': datetime(2020, 5, 15, tzinfo=timezone.utc)}
                ),
                # Sequence that starts before containing Section.
                (
                    cls.seq_before_key,
                    {'start': datetime(2020, 5, 14, tzinfo=timezone.utc)}
                ),
                # Sequence starts at same time as containing Section.
                (
                    cls.seq_same_key,
                    {'start': datetime(2020, 5, 15, tzinfo=timezone.utc)}
                ),
                # Sequence starts after containing Section.
                (
                    cls.seq_after_key,
                    {'start': datetime(2020, 5, 16, tzinfo=timezone.utc)}
                ),
                # Sequence should inherit start information from Section.
                (
                    cls.seq_inherit_key,
                    {'start': None}
                ),
                # Sequence should inherit start information from Section, but has a due date set.
                (
                    cls.seq_due_key,
                    {
                        'start': None,
                        'due': datetime(2020, 5, 20, tzinfo=timezone.utc)
                    }
                ),
            ]
        )
        visibility = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=False
        )
        cls.outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            days_early_for_beta=None,
            course_visibility=CourseVisibility.PRIVATE,
            sections=[
                CourseSectionData(
                    usage_key=cls.section_key,
                    title="Section",
                    visibility=visibility,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=cls.seq_before_key,
                            title='Before',
                            visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_same_key,
                            title='Same', visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_after_key,
                            title='After',
                            visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_inherit_key,
                            title='Inherit',
                            visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_due_key,
                            title='Due',
                            visibility=visibility,
                            inaccessible_after_due=True
                        ),
                    ]
                )
            ],
            self_paced=False,
        )
        replace_course_outline(cls.outline)

        # Enroll student in the course
        cls.student.courseenrollment_set.create(course_id=cls.course_key, is_active=True, mode="audit")
        # Enroll beta tester in the course
        cls.beta_tester.courseenrollment_set.create(course_id=cls.course_key, is_active=True, mode="audit")
        assert user_has_role(cls.beta_tester, CourseBetaTesterRole(cls.course_key))
        assert cls.outline.days_early_for_beta is None

    def get_details(self, at_time):
        staff_details = get_user_course_outline_details(self.course_key, self.global_staff, at_time)
        student_details = get_user_course_outline_details(self.course_key, self.student, at_time)
        beta_tester_details = get_user_course_outline_details(self.course_key, self.beta_tester, at_time)
        return staff_details, student_details, beta_tester_details

    def get_sequence_keys(self, exclude=None):
        if exclude is None:
            exclude = []
        if not isinstance(exclude, list):
            raise TypeError("`exclude` must be a list of keys to be excluded")
        return [key for key in self.all_seq_keys if key not in exclude]

    def test_before_course_starts(self):
        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 9, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5
        # Student can access nothing
        assert len(student_details.outline.accessible_sequences) == 0
        # Beta tester can access nothing
        assert len(beta_tester_details.outline.accessible_sequences) == 0

        # Everyone can see everything
        assert len(staff_details.outline.sequences) == 5
        assert len(student_details.outline.sequences) == 5
        assert len(beta_tester_details.outline.sequences) == 5

    def test_course_beta_access(self):
        course_outline = attr.evolve(self.outline, days_early_for_beta=6)
        assert course_outline.days_early_for_beta is not None
        replace_course_outline(course_outline)

        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 9, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5
        # Student can access nothing
        assert len(student_details.outline.accessible_sequences) == 0
        # Beta tester can access some
        assert len(beta_tester_details.outline.accessible_sequences) == 4

        # Everyone can see everything
        assert len(staff_details.outline.sequences) == 5
        assert len(student_details.outline.sequences) == 5
        assert len(beta_tester_details.outline.sequences) == 5

    def test_before_section_starts(self):
        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 14, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access nothing -- even though one of the sequences is set
        # to start on 2020-05-14, it's not available because the section hasn't
        # started yet.
        assert len(student_details.outline.accessible_sequences) == 0
        before_seq_sched_item_data = student_details.schedule.sequences[self.seq_before_key]
        assert before_seq_sched_item_data.start == datetime(2020, 5, 14, tzinfo=timezone.utc)
        assert before_seq_sched_item_data.effective_start == datetime(2020, 5, 15, tzinfo=timezone.utc)

        # Beta tester can access nothing
        assert len(beta_tester_details.outline.accessible_sequences) == 0

    def test_section_beta_access(self):
        course_outline = attr.evolve(self.outline, days_early_for_beta=1)
        assert course_outline.days_early_for_beta is not None
        replace_course_outline(course_outline)

        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 14, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access nothing -- even though one of the sequences is set
        # to start on 2020-05-14, it's not available because the section hasn't
        # started yet.
        assert len(student_details.outline.accessible_sequences) == 0
        before_seq_sched_item_data = student_details.schedule.sequences[self.seq_before_key]
        assert before_seq_sched_item_data.start == datetime(2020, 5, 14, tzinfo=timezone.utc)
        assert before_seq_sched_item_data.effective_start == datetime(2020, 5, 15, tzinfo=timezone.utc)

        # Beta tester can access some
        assert len(beta_tester_details.outline.accessible_sequences) == 4

    def test_at_section_start(self):
        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 15, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access all sequences except the one that starts after this
        # datetime (self.seq_after_key)
        assert len(student_details.outline.accessible_sequences) == 4
        assert self.seq_after_key not in student_details.outline.accessible_sequences
        for key in self.get_sequence_keys(exclude=[self.seq_after_key]):
            assert key in student_details.outline.accessible_sequences

        # Beta tester can access same as student
        assert len(beta_tester_details.outline.accessible_sequences) == 4

    def test_at_beta_section_start(self):
        course_outline = attr.evolve(self.outline, days_early_for_beta=1)
        assert course_outline.days_early_for_beta is not None
        replace_course_outline(course_outline)

        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 15, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access all sequences except the one that starts after this
        # datetime (self.seq_after_key)
        assert len(student_details.outline.accessible_sequences) == 4
        assert self.seq_after_key not in student_details.outline.accessible_sequences
        for key in self.get_sequence_keys(exclude=[self.seq_after_key]):
            assert key in student_details.outline.accessible_sequences

        # Beta tester can access all
        assert len(beta_tester_details.outline.accessible_sequences) == 5

    def test_is_due_and_before_due(self):
        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 16, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access all sequences including the one that is due in
        # the future (self.seq_due_key)
        assert len(student_details.outline.accessible_sequences) == 5
        assert self.seq_due_key in student_details.outline.accessible_sequences

        seq_due_sched_item_data = student_details.schedule.sequences[self.seq_due_key]
        assert seq_due_sched_item_data.due == datetime(2020, 5, 20, tzinfo=timezone.utc)

        # Beta tester can access some
        assert len(beta_tester_details.outline.accessible_sequences) == 5

    def test_is_due_and_after_due(self):
        staff_details, student_details, beta_tester_details = self.get_details(
            datetime(2020, 5, 21, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 5

        # Student can access all sequences except the one that is due before this
        # datetime (self.seq_due_key)
        assert len(student_details.outline.accessible_sequences) == 4
        assert self.seq_due_key not in student_details.outline.accessible_sequences
        assert self.seq_due_key in student_details.outline.sequences
        for key in self.get_sequence_keys(exclude=[self.seq_due_key]):
            assert key in student_details.outline.accessible_sequences

        # Beta tester can access same as student
        assert len(beta_tester_details.outline.accessible_sequences) == 4


class SelfPacedCourseOutlineTestCase(CacheIsolationTestCase):
    @classmethod
    def setUpTestData(cls):
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )

        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")

        # The UsageKeys we're going to set up for date tests.
        cls.section_key = cls.course_key.make_usage_key('chapter', 'ch1')

        # Sequence with due date
        cls.seq_due_key = cls.course_key.make_usage_key('sequential', 'seq')

        # Sequence with due date and "inaccessible after due" enabled
        cls.seq_hide_after_due_key = cls.course_key.make_usage_key('sequential', 'seq_hide_after_due_key')

        # Set scheduling information into edx-when for a single Section with
        # two sequences with due date
        set_dates_for_course(
            cls.course_key,
            [
                (
                    cls.course_key.make_usage_key('course', 'course'),
                    {
                        'start': datetime(2020, 5, 10, tzinfo=timezone.utc),
                    }
                ),
                (
                    cls.section_key,
                    {'start': datetime(2020, 5, 15, tzinfo=timezone.utc)}
                ),
                (
                    cls.seq_due_key,
                    {'due': datetime(2020, 5, 21, tzinfo=timezone.utc)}
                ),
                (
                    cls.seq_hide_after_due_key,
                    {'due': datetime(2020, 5, 21, tzinfo=timezone.utc)}
                ),
            ]
        )
        visibility = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=False
        )
        cls.outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            days_early_for_beta=None,
            course_visibility=CourseVisibility.PRIVATE,
            sections=[
                CourseSectionData(
                    usage_key=cls.section_key,
                    title="Section",
                    visibility=visibility,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=cls.seq_due_key,
                            title='Due',
                            visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_hide_after_due_key,
                            title='Inaccessible after due',
                            visibility=visibility,
                            inaccessible_after_due=True
                        ),
                    ],
                ),
            ],
            self_paced=True,
        )

        replace_course_outline(cls.outline)

        # Enroll student in the course
        cls.student.courseenrollment_set.create(course_id=cls.course_key, is_active=True, mode="audit")

    def test_sequences_accessible_after_due(self):
        at_time = datetime(2020, 5, 22, tzinfo=timezone.utc)
        staff_outline = get_user_course_outline_details(self.course_key, self.global_staff, at_time).outline
        student_outline = get_user_course_outline_details(self.course_key, self.student, at_time).outline

        # Staff can always access all sequences
        assert len(staff_outline.accessible_sequences) == 2

        # In self-paced course, due date of sequences equals to due date of
        # course, so here student should see all sequences, even if their
        # due dates explicitly were set before end of course
        assert len(student_outline.accessible_sequences) == 2


class VisbilityTestCase(CacheIsolationTestCase):
    """
    Visibility-related tests.
    """

    @classmethod
    def setUpTestData(cls):
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )
        cls.anonymous_user = AnonymousUser()

        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")

        # The UsageKeys we're going to set up for date tests.
        cls.normal_section_key = cls.course_key.make_usage_key('chapter', 'normal_section')
        cls.staff_section_key = cls.course_key.make_usage_key('chapter', 'staff_only_section')

        cls.staff_in_normal_key = cls.course_key.make_usage_key('sequential', 'staff_in_normal')
        cls.hide_in_normal_key = cls.course_key.make_usage_key('sequential', 'hide_in_normal')
        cls.due_in_normal_key = cls.course_key.make_usage_key('sequential', 'due_in_normal')
        cls.normal_in_normal_key = cls.course_key.make_usage_key('sequential', 'normal_in_normal')
        cls.normal_in_staff_key = cls.course_key.make_usage_key('sequential', 'normal_in_staff')

        v_normal = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=False
        )
        v_hide_from_toc = VisibilityData(
            hide_from_toc=True,
            visible_to_staff_only=False
        )
        v_staff_only = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=True
        )

        cls.outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            days_early_for_beta=None,
            course_visibility=CourseVisibility.PRIVATE,
            sections=[
                CourseSectionData(
                    usage_key=cls.normal_section_key,
                    title="Normal Section",
                    visibility=v_normal,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=cls.staff_in_normal_key, title='Before', visibility=v_staff_only
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.hide_in_normal_key, title='Same', visibility=v_hide_from_toc
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.normal_in_normal_key, title='After', visibility=v_normal
                        ),
                    ]
                ),
                CourseSectionData(
                    usage_key=cls.staff_section_key,
                    title="Staff Only Section",
                    visibility=v_staff_only,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=cls.normal_in_staff_key, title='Before', visibility=v_normal
                        ),
                    ]
                )

            ],
            self_paced=False
        )
        replace_course_outline(cls.outline)

        # Enroll student in the course
        cls.student.courseenrollment_set.create(course_id=cls.course_key, is_active=True, mode="audit")

    def test_visibility(self):
        at_time = datetime(2020, 5, 21, tzinfo=timezone.utc)  # Exact value doesn't matter
        staff_outline = get_user_course_outline_details(self.course_key, self.global_staff, at_time).outline
        student_outline = get_user_course_outline_details(self.course_key, self.student, at_time).outline

        # Sections visible
        assert len(staff_outline.sections) == 2
        assert len(student_outline.sections) == 1

        # Sequences visible
        assert len(staff_outline.sequences) == 4
        assert len(student_outline.sequences) == 1
        assert self.normal_in_normal_key in student_outline.sequences


class SequentialVisibilityTestCase(CacheIsolationTestCase):
    """
    Tests sequentials visibility under different course visibility settings i.e public, public_outline, private
    and different types of users e.g unenrolled, enrolled, anonymous, staff
    """

    @classmethod
    def setUpTestData(cls):
        super(SequentialVisibilityTestCase, cls).setUpTestData()

        cls.global_staff = User.objects.create_user('global_staff', email='gstaff@example.com', is_staff=True)
        cls.student = User.objects.create_user('student', email='student@example.com', is_staff=False)
        cls.unenrolled_student = User.objects.create_user('unenrolled', email='unenrolled@example.com', is_staff=False)
        cls.anonymous_user = AnonymousUser()

        # Handy variable as we almost always need to test with all types of users
        cls.all_users = [cls.global_staff, cls.student, cls.unenrolled_student, cls.anonymous_user]

        cls.course_access_time = datetime(2020, 5, 21, tzinfo=timezone.utc)  # Some random time in past

        # Create course, set it start date to some time in past and attach outline to it
        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T0")
        set_dates_for_course(
            cls.course_key, [(cls.course_key.make_usage_key('course', 'course'), {'start': cls.course_access_time})]
        )
        cls.course_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            days_early_for_beta=None,
            sections=generate_sections(cls.course_key, [2, 1, 3]),
            self_paced=False,
            course_visibility=CourseVisibility.PRIVATE
        )
        replace_course_outline(cls.course_outline)

        # enroll student into the course
        cls.student.courseenrollment_set.create(course_id=cls.course_key, is_active=True, mode="audit")

    @override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, active=True)
    def test_public_course_outline(self):
        """Test that public course outline is the same for everyone."""
        course_outline = attr.evolve(self.course_outline, course_visibility=CourseVisibility.PUBLIC)
        replace_course_outline(course_outline)

        for user in self.all_users:
            with self.subTest(user=user):
                user_course_outline = get_user_course_outline(self.course_key, user, self.course_access_time)

                self.assertEqual(len(user_course_outline.sections), 3)
                self.assertEqual(len(user_course_outline.sequences), 6)
                self.assertTrue(
                    all([
                        seq.usage_key in user_course_outline.accessible_sequences
                        for seq in user_course_outline.sequences.values()
                    ]),
                    "Sequences should be accessible to all users for a public course"
                )

    @override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, active=True)
    def test_public_outline_course_outline(self):
        """
        Test that a course with public_outline access has same outline for everyone
        except that the links are not accessible for non-enrolled and anonymous user.
        """
        course_outline = attr.evolve(self.course_outline, course_visibility=CourseVisibility.PUBLIC_OUTLINE)
        replace_course_outline(course_outline)

        for user in self.all_users:
            with self.subTest(user=user):
                user_course_outline = get_user_course_outline(self.course_key, user, self.course_access_time)

                self.assertEqual(len(user_course_outline.sections), 3)
                self.assertEqual(len(user_course_outline.sequences), 6)

                is_sequence_accessible = [
                    seq.usage_key in user_course_outline.accessible_sequences
                    for seq in user_course_outline.sequences.values()
                ]

                if user in [self.anonymous_user, self.unenrolled_student]:
                    self.assertTrue(
                        all(not is_accessible for is_accessible in is_sequence_accessible),
                        "Sequences shouldn't be accessible to anonymous or non-enrolled students "
                        "for a public_outline course"
                    )
                else:
                    self.assertTrue(
                        all(is_sequence_accessible),
                        "Sequences should be accessible to enrolled, staff users for a public_outline course"
                    )

    @override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, active=True)
    def test_private_course_outline(self):
        """
        Test that the outline of a course with private access is only accessible/visible
        to enrolled user or staff.
        """
        course_outline = attr.evolve(self.course_outline, course_visibility=CourseVisibility.PRIVATE)
        replace_course_outline(course_outline)

        for user in self.all_users:
            with self.subTest(user=user):
                user_course_outline = get_user_course_outline(self.course_key, user, self.course_access_time)

                is_sequence_accessible = [
                    seq.usage_key in user_course_outline.accessible_sequences
                    for seq in user_course_outline.sequences.values()
                ]

                if user in [self.anonymous_user, self.unenrolled_student]:
                    self.assertTrue(
                        len(user_course_outline.sections) == len(user_course_outline.sequences) == 0,
                        "No section of a private course should be visible to anonymous or non-enrolled student"
                    )
                else:
                    # Enrolled or Staff User
                    self.assertEqual(len(user_course_outline.sections), 3)
                    self.assertEqual(len(user_course_outline.sequences), 6)
                    self.assertTrue(
                        all(is_sequence_accessible),
                        "Sequences should be accessible to enrolled, staff users for a public_outline course"
                    )
