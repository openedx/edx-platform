"""
Tests for the edx_proctoring integration into Studio
"""

from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from contentstore.signals import listen_for_course_publish

from edx_proctoring.api import get_all_exams_for_course


class TestProctoredExams(ModuleStoreTestCase):
    """
    Tests for the publishing of proctored exams
    """

    def setUp(self):
        """
        Initial data setup
        """
        super(TestProctoredExams, self).setUp()

        self.course = CourseFactory.create(
            org='edX',
            course='900',
            run='test_run',
            enable_proctored_exams=True
        )

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PROCTORED_EXAMS': True})
    def test_publishing_proctored_exam(self):
        """
        Happy path testing to see that when a course is published which contains
        a proctored exam, it will also put an entry into the exam tables
        """

        chapter = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        sequence = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_mins=10,
            is_proctored_enabled=True
        )

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))

        self.assertEqual(len(exams), 1)

        exam = exams[0]
        self.assertEqual(exam['course_id'], unicode(self.course.id))
        self.assertEqual(exam['content_id'], unicode(sequence.location))
        self.assertEqual(exam['exam_name'], sequence.display_name)
        self.assertEqual(exam['time_limit_mins'], sequence.default_time_limit_mins)
        self.assertEqual(exam['is_proctored'], sequence.is_proctored_enabled)
        self.assertEqual(exam['is_active'], True)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PROCTORED_EXAMS': True})
    def test_publishing_timed_exam(self):
        """
        Happy path testing to see that when a course is published which contains
        a timed exam, it will also put an entry into the exam tables
        """

        chapter = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        sequence = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_mins=10,
            is_proctored_enabled=False
        )

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))

        self.assertEqual(len(exams), 1)

        exam = exams[0]
        self.assertEqual(exam['course_id'], unicode(self.course.id))
        self.assertEqual(exam['content_id'], unicode(sequence.location))
        self.assertEqual(exam['exam_name'], sequence.display_name)
        self.assertEqual(exam['time_limit_mins'], sequence.default_time_limit_mins)
        self.assertEqual(exam['is_proctored'], sequence.is_proctored_enabled)
        self.assertEqual(exam['is_active'], True)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PROCTORED_EXAMS': True})
    def test_unpublishing_proctored_exam(self):
        """
        Make sure that if we publish and then unpublish a proctored exam,
        the exam record stays, but is marked as is_active=False
        """

        chapter = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        sequence = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_mins=10,
            is_proctored_enabled=True
        )

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))
        self.assertEqual(len(exams), 1)

        sequence.is_time_limited = False
        sequence.is_proctored_enabled = False

        self.store.update_item(sequence, self.user.id)

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))
        self.assertEqual(len(exams), 1)

        exam = exams[0]
        self.assertEqual(exam['is_active'], False)

    def test_dangling_exam(self):
        """
        Make sure we filter out all dangling items
        """

        chapter = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        sequence = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_mins=10,
            is_proctored_enabled=True
        )

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))
        self.assertEqual(len(exams), 1)

        self.store.delete_item(chapter.location, self.user.id)

        # republish course
        listen_for_course_publish(self, self.course.id)

        # look through exam table, the dangling exam
        # should be disabled
        exams = get_all_exams_for_course(unicode(self.course.id))
        self.assertEqual(len(exams), 1)

        exam = exams[0]
        self.assertEqual(exam['is_active'], False)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PROCTORED_EXAMS': False})
    def test_feature_flag_off(self):
        """
        Make sure the feature flag is honored
        """

        chapter = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_mins=10,
            is_proctored_enabled=True
        )

        listen_for_course_publish(self, self.course.id)

        exams = get_all_exams_for_course(unicode(self.course.id))
        self.assertEqual(len(exams), 0)
