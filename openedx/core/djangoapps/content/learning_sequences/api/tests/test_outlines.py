"""
Top level API tests. Tests API public contracts only. Do not import/create/mock
models for this app.
"""
from datetime import datetime, timezone

from django.contrib.auth.models import User, AnonymousUser
from edx_when.api import set_dates_for_course
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator
import attr

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from ..data import (
    CourseOutlineData, CourseSectionData, CourseLearningSequenceData,
    VisibilityData
)
from ..outlines import (
    get_course_outline, get_user_course_outline,
    get_user_course_outline_details, replace_course_outline
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
            hide_from_toc=False, visible_to_staff_only=False
        )
        cls.course_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="Roundtrip Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2015",
            sections=generate_sections(cls.course_key, [2, 2]),
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
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )
        # TODO: Add AnonymousUser here.

        # Seed with data
        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")
        normal_visibility = VisibilityData(
            hide_from_toc=False, visible_to_staff_only=False
        )
        cls.simple_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            sections=generate_sections(cls.course_key, [2, 1, 3])
        )
        replace_course_outline(cls.simple_outline)

    def test_simple_outline(self):
        """This outline is the same for everyone."""
        at_time = datetime(2020, 5, 21, tzinfo=timezone.utc)
        student_outline = get_user_course_outline(
            self.course_key, self.student, at_time
        )
        global_staff_outline = get_user_course_outline(
            self.course_key, self.global_staff, at_time
        )
        assert student_outline.sections == global_staff_outline.sections
        assert student_outline.at_time == at_time

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
        # Users...
        cls.global_staff = User.objects.create_user(
            'global_staff', email='gstaff@example.com', is_staff=True
        )
        cls.student = User.objects.create_user(
            'student', email='student@example.com', is_staff=False
        )
        # TODO: Add AnonymousUser here.

        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")

        # The UsageKeys we're going to set up for date tests.
        cls.section_key = cls.course_key.make_usage_key('chapter', 'ch1')
        cls.seq_before_key = cls.course_key.make_usage_key('sequential', 'seq_before')
        cls.seq_same_key = cls.course_key.make_usage_key('sequential', 'seq_same')
        cls.seq_after_key = cls.course_key.make_usage_key('sequential', 'seq_after')
        cls.seq_inherit_key = cls.course_key.make_usage_key('sequential', 'seq_inherit')

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
            ]
        )
        visibility = VisibilityData(hide_from_toc=False, visible_to_staff_only=False)
        cls.outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
            sections=[
                CourseSectionData(
                    usage_key=cls.section_key,
                    title="Section",
                    visibility=visibility,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=cls.seq_before_key, title='Before', visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_same_key, title='Same', visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_after_key, title='After', visibility=visibility
                        ),
                        CourseLearningSequenceData(
                            usage_key=cls.seq_inherit_key, title='Inherit', visibility=visibility
                        ),
                    ]
                )
            ]
        )
        replace_course_outline(cls.outline)

    def get_details(self, at_time):
        staff_details = get_user_course_outline_details(self.course_key, self.global_staff, at_time)
        student_details = get_user_course_outline_details(self.course_key, self.student, at_time)
        return staff_details, student_details

    def test_before_course_starts(self):
        staff_details, student_details = self.get_details(
            datetime(2020, 5, 9, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 4
        # Student can access nothing
        assert len(student_details.outline.accessible_sequences) == 0

        # Everyone can see everything
        assert len(staff_details.outline.sequences) == 4
        assert len(student_details.outline.sequences) == 4

    def test_before_section_starts(self):
        staff_details, student_details = self.get_details(
            datetime(2020, 5, 14, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 4

        # Student can access nothing -- even though one of the sequences is set
        # to start on 2020-05-14, it's not available because the section hasn't
        # started yet.
        assert len(student_details.outline.accessible_sequences) == 0
        before_seq_sched_item_data = student_details.schedule.sequences[self.seq_before_key]
        assert before_seq_sched_item_data.start == datetime(2020, 5, 14, tzinfo=timezone.utc)
        assert before_seq_sched_item_data.effective_start == datetime(2020, 5, 15, tzinfo=timezone.utc)

    def test_at_section_start(self):
        staff_details, student_details = self.get_details(
            datetime(2020, 5, 15, tzinfo=timezone.utc)
        )
        # Staff can always access all sequences
        assert len(staff_details.outline.accessible_sequences) == 4

        # Student can access all sequences except the one that starts after this
        # datetime (self.seq_after_key)
        assert len(student_details.outline.accessible_sequences) == 3
        assert self.seq_before_key in student_details.outline.accessible_sequences
        assert self.seq_same_key in student_details.outline.accessible_sequences
        assert self.seq_inherit_key in student_details.outline.accessible_sequences


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
        # TODO: Add AnonymousUser here.
        cls.course_key = CourseKey.from_string("course-v1:OpenEdX+Outline+T1")

        # The UsageKeys we're going to set up for date tests.
        cls.normal_section_key = cls.course_key.make_usage_key('chapter', 'normal_section')
        cls.staff_section_key = cls.course_key.make_usage_key('chapter', 'staff_only_section')

        cls.staff_in_normal_key = cls.course_key.make_usage_key('sequential', 'staff_in_normal')
        cls.hide_in_normal_key = cls.course_key.make_usage_key('sequential', 'hide_in_normal')
        cls.normal_in_normal_key = cls.course_key.make_usage_key('sequential', 'normal_in_normal')
        cls.normal_in_staff_key = cls.course_key.make_usage_key('sequential', 'normal_in_staff')

        v_normal = VisibilityData(hide_from_toc=False, visible_to_staff_only=False)
        v_hide_from_toc = VisibilityData(hide_from_toc=True, visible_to_staff_only=False)
        v_staff_only = VisibilityData(hide_from_toc=False, visible_to_staff_only=True)

        cls.outline = CourseOutlineData(
            course_key=cls.course_key,
            title="User Outline Test Course!",
            published_at=datetime(2020, 5, 20, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2020",
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

            ]
        )
        replace_course_outline(cls.outline)

    def test_visibility(self):
        at_time = datetime(2020, 5, 21, tzinfo=timezone.utc)  # Exact value doesn't matter
        staff_details = get_user_course_outline_details(self.course_key, self.global_staff, at_time)
        student_details = get_user_course_outline_details(self.course_key, self.student, at_time)

        # Sections visible
        assert len(staff_details.outline.sections) == 2
        assert len(student_details.outline.sections) == 1

        # Sequences visible
        assert len(staff_details.outline.sequences) == 4
        assert len(student_details.outline.sequences) == 1
        assert self.normal_in_normal_key in student_details.outline.sequences
