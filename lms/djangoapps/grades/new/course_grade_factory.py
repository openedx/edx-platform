from collections import namedtuple
import dogstats_wrapper as dog_stats_api
from logging import getLogger

from openedx.core.djangoapps.content.block_structure.api import get_block_structure_manager
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_CHANGED

from ..config import assume_zero_if_absent, should_persist_grades
from ..config.waffle import waffle, WRITE_ONLY_IF_ENGAGED
from ..models import PersistentCourseGrade
from .course_data import CourseData
from .course_grade import CourseGrade, ZeroCourseGrade


log = getLogger(__name__)


class CourseGradeFactory(object):
    """
    Factory class to create Course Grade objects.
    """
    GradeResult = namedtuple('GradeResult', ['student', 'course_grade', 'err_msg'])

    def create(self, user, course=None, collected_block_structure=None, course_structure=None, course_key=None):
        """
        Returns the CourseGrade for the given user in the course.
        Reads the value from storage and validates that the grading
        policy hasn't changed since the grade was last computed.
        If not in storage, returns a ZeroGrade if ASSUME_ZERO_GRADE_IF_ABSENT.
        Else, if changed or not in storage, computes and returns a new value.

        At least one of course, collected_block_structure, course_structure,
        or course_key should be provided.
        """
        course_data = CourseData(user, course, collected_block_structure, course_structure, course_key)
        try:
            course_grade, read_policy_hash = self._read(user, course_data)
            if read_policy_hash == course_data.grading_policy_hash:
                return course_grade
            read_only = False  # update the persisted grade since the policy changed; TODO(TNL-6786) remove soon
        except PersistentCourseGrade.DoesNotExist:
            if assume_zero_if_absent(course_data.course_key):
                return self._create_zero(user, course_data)
            read_only = True  # keep the grade un-persisted; TODO(TNL-6786) remove once all grades are backfilled

        return self._update(user, course_data, read_only)

    def read(self, user, course=None, collected_block_structure=None, course_structure=None, course_key=None):
        """
        Returns the CourseGrade for the given user in the course as
        persisted in storage.  Does NOT verify whether the grading
        policy is still valid since the grade was last computed.
        If not in storage, returns a ZeroGrade if ASSUME_ZERO_GRADE_IF_ABSENT
        else returns None.

        At least one of course, collected_block_structure, course_structure,
        or course_key should be provided.
        """
        course_data = CourseData(user, course, collected_block_structure, course_structure, course_key)
        try:
            course_grade, _ = self._read(user, course_data)
            return course_grade
        except PersistentCourseGrade.DoesNotExist:
            if assume_zero_if_absent(course_data.course_key):
                return self._create_zero(user, course_data)
            else:
                return None

    def update(self, user, course=None, collected_block_structure=None, course_structure=None, course_key=None):
        """
        Computes, updates, and returns the CourseGrade for the given
        user in the course.

        At least one of course, collected_block_structure, course_structure,
        or course_key should be provided.
        """
        course_data = CourseData(user, course, collected_block_structure, course_structure, course_key)
        return self._update(user, course_data, read_only=False)

    def iter(self, course, students, force_update=False):
        """
        Given a course and an iterable of students (User), yield a GradeResult
        for every student enrolled in the course.  GradeResult is a named tuple of:

            (student, course_grade, err_msg)

        If an error occurred, course_grade will be None and err_msg will be an
        exception message. If there was no error, err_msg is an empty string.
        """
        # Pre-fetch the collected course_structure so:
        # 1. Correctness: the same version of the course is used to
        #    compute the grade for all students.
        # 2. Optimization: the collected course_structure is not
        #    retrieved from the data store multiple times.

        collected_block_structure = get_block_structure_manager(course.id).get_collected()
        for student in students:
            with dog_stats_api.timer('lms.grades.CourseGradeFactory.iter', tags=[u'action:{}'.format(course.id)]):
                try:
                    operation = CourseGradeFactory().update if force_update else CourseGradeFactory().create
                    course_grade = operation(student, course, collected_block_structure)
                    yield self.GradeResult(student, course_grade, "")

                except Exception as exc:  # pylint: disable=broad-except
                    # Keep marching on even if this student couldn't be graded for
                    # some reason, but log it for future reference.
                    log.exception(
                        'Cannot grade student %s (%s) in course %s because of exception: %s',
                        student.username,
                        student.id,
                        course.id,
                        exc.message
                    )
                    yield self.GradeResult(student, None, exc.message)

    @staticmethod
    def _create_zero(user, course_data):
        """
        Returns a ZeroCourseGrade object for the given user and course.
        """
        log.info(u'Grades: CreateZero, %s, User: %s', unicode(course_data), user.id)
        return ZeroCourseGrade(user, course_data)

    @staticmethod
    def _read(user, course_data):
        """
        Returns a CourseGrade object based on stored grade information
        for the given user and course.
        """
        if not should_persist_grades(course_data.course_key):
            raise PersistentCourseGrade.DoesNotExist

        persistent_grade = PersistentCourseGrade.read_course_grade(user.id, course_data.course_key)
        course_grade = CourseGrade(
            user,
            course_data,
            persistent_grade.percent_grade,
            persistent_grade.letter_grade,
            persistent_grade.passed_timestamp is not None,
        )
        log.info(u'Grades: Read, %s, User: %s, %s', unicode(course_data), user.id, persistent_grade)

        return course_grade, persistent_grade.grading_policy_hash

    @staticmethod
    def _update(user, course_data, read_only):
        """
        Computes, saves, and returns a CourseGrade object for the
        given user and course.
        Sends a COURSE_GRADE_CHANGED signal to listeners.
        """
        course_grade = CourseGrade(user, course_data)
        course_grade.update()

        should_persist = (
            (not read_only) and  # TODO(TNL-6786) Remove the read_only boolean once all grades are back-filled.
            should_persist_grades(course_data.course_key) and
            (not waffle().is_enabled(WRITE_ONLY_IF_ENGAGED) or course_grade.attempted)
        )
        if should_persist:
            course_grade._subsection_grade_factory.bulk_create_unsaved()
            PersistentCourseGrade.update_or_create_course_grade(
                user_id=user.id,
                course_id=course_data.course_key,
                course_version=course_data.version,
                course_edited_timestamp=course_data.edited_on,
                grading_policy_hash=course_data.grading_policy_hash,
                percent_grade=course_grade.percent,
                letter_grade=course_grade.letter_grade or "",
                passed=course_grade.passed,
            )

        COURSE_GRADE_CHANGED.send_robust(
            sender=None,
            user=user,
            course_grade=course_grade,
            course_key=course_data.course_key,
            deadline=course_data.course.end,
        )

        log.info(
            u'Grades: Update, %s, User: %s, %s, persisted: %s',
            course_data.full_string(), user.id, course_grade, should_persist,
        )

        return course_grade
