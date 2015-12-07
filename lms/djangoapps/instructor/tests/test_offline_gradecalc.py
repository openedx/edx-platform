"""
Tests for offline_gradecalc.py
"""
import json
from mock import patch

from courseware.models import OfflineComputedGrade
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.graders import Score
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..offline_gradecalc import offline_grade_calculation, student_grades


def mock_grade(_student, _request, course, **_kwargs):
    """ Return some fake grade data to mock grades.grade() """
    return {
        'grade': u'Pass',
        'totaled_scores': {
            u'Homework': [
                Score(earned=10.0, possible=10.0, graded=True, section=u'Subsection 1', module_id=None),
            ]
        },
        'percent': 0.85,
        'raw_scores': [
            Score(
                earned=5.0, possible=5.0, graded=True, section=u'Numerical Input',
                module_id=course.id.make_usage_key('problem', 'problem1'),
            ),
            Score(
                earned=5.0, possible=5.0, graded=True, section=u'Multiple Choice',
                module_id=course.id.make_usage_key('problem', 'problem2'),
            ),
        ],
        'section_breakdown': [
            {'category': u'Homework', 'percent': 1.0, 'detail': u'Homework 1 - Test - 100% (10/10)', 'label': u'HW 01'},
            {'category': u'Final Exam', 'prominent': True, 'percent': 0, 'detail': u'Final = 0%', 'label': u'Final'}
        ],
        'grade_breakdown': [
            {'category': u'Homework', 'percent': 0.85, 'detail': u'Homework = 85.00% of a possible 85.00%'},
            {'category': u'Final Exam', 'percent': 0.0, 'detail': u'Final Exam = 0.00% of a possible 15.00%'}
        ]
    }


class TestOfflineGradeCalc(ModuleStoreTestCase):
    """ Test Offline Grade Calculation with some mocked grades """
    def setUp(self):
        super(TestOfflineGradeCalc, self).setUp()

        with modulestore().default_store(ModuleStoreEnum.Type.split):  # Test with split b/c old mongo keys are messy
            self.course = CourseFactory.create()
        self.user = UserFactory.create()
        CourseEnrollment.enroll(self.user, self.course.id)

        patcher = patch('courseware.grades.grade', new=mock_grade)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_output(self):
        offline_grades = OfflineComputedGrade.objects
        self.assertEqual(offline_grades.filter(user=self.user, course_id=self.course.id).count(), 0)
        offline_grade_calculation(self.course.id)
        result = offline_grades.get(user=self.user, course_id=self.course.id)
        decoded = json.loads(result.gradeset)
        self.assertEqual(decoded['grade'], "Pass")
        self.assertEqual(decoded['percent'], 0.85)
        self.assertEqual(decoded['totaled_scores'], {
            "Homework": [
                {"earned": 10.0, "possible": 10.0, "graded": True, "section": "Subsection 1", "module_id": None}
            ]
        })
        self.assertEqual(decoded['raw_scores'], [
            {
                "earned": 5.0,
                "possible": 5.0,
                "graded": True,
                "section": "Numerical Input",
                "module_id": unicode(self.course.id.make_usage_key('problem', 'problem1')),
            },
            {
                "earned": 5.0,
                "possible": 5.0,
                "graded": True,
                "section": "Multiple Choice",
                "module_id": unicode(self.course.id.make_usage_key('problem', 'problem2')),
            }
        ])
        self.assertEqual(decoded['section_breakdown'], [
            {"category": "Homework", "percent": 1.0, "detail": "Homework 1 - Test - 100% (10/10)", "label": "HW 01"},
            {"category": "Final Exam", "label": "Final", "percent": 0, "detail": "Final = 0%", "prominent": True}
        ])
        self.assertEqual(decoded['grade_breakdown'], [
            {"category": "Homework", "percent": 0.85, "detail": "Homework = 85.00% of a possible 85.00%"},
            {"category": "Final Exam", "percent": 0.0, "detail": "Final Exam = 0.00% of a possible 15.00%"}
        ])

    def test_student_grades(self):
        """ Test that the data returned by student_grades() and grades.grade() match """
        offline_grade_calculation(self.course.id)
        with patch('courseware.grades.grade', side_effect=AssertionError('Should not re-grade')):
            result = student_grades(self.user, None, self.course, use_offline=True)
        self.assertEqual(result, mock_grade(self.user, None, self.course))
