"""Grading tests"""
import unittest

from xmodule import graders
from xmodule.graders import Score, aggregate_scores


class GradesheetTest(unittest.TestCase):
    '''Tests the aggregate_scores method'''

    def test_weighted_grading(self):
        scores = []
        Score.__sub__ = lambda me, other: (me.earned - other.earned) + (me.possible - other.possible)

        all_total, graded_total = aggregate_scores(scores)
        self.assertEqual(all_total, Score(earned=0, possible=0, graded=False, section="summary", module_id=None))
        self.assertEqual(graded_total, Score(earned=0, possible=0, graded=True, section="summary", module_id=None))

        scores.append(Score(earned=0, possible=5, graded=False, section="summary", module_id=None))
        all_total, graded_total = aggregate_scores(scores)
        self.assertEqual(all_total, Score(earned=0, possible=5, graded=False, section="summary", module_id=None))
        self.assertEqual(graded_total, Score(earned=0, possible=0, graded=True, section="summary", module_id=None))

        scores.append(Score(earned=3, possible=5, graded=True, section="summary", module_id=None))
        all_total, graded_total = aggregate_scores(scores)
        self.assertAlmostEqual(all_total, Score(earned=3, possible=10, graded=False, section="summary", module_id=None))
        self.assertAlmostEqual(
            graded_total, Score(earned=3, possible=5, graded=True, section="summary", module_id=None)
        )

        scores.append(Score(earned=2, possible=5, graded=True, section="summary", module_id=None))
        all_total, graded_total = aggregate_scores(scores)
        self.assertAlmostEqual(all_total, Score(earned=5, possible=15, graded=False, section="summary", module_id=None))
        self.assertAlmostEqual(
            graded_total, Score(earned=5, possible=10, graded=True, section="summary", module_id=None)
        )


class GraderTest(unittest.TestCase):
    '''Tests grader implementations'''

    empty_gradesheet = {
    }

    incomplete_gradesheet = {
        'Homework': [],
        'Lab': [],
        'Midterm': [],
    }

    test_gradesheet = {
        'Homework': [Score(earned=2, possible=20.0, graded=True, section='hw1', module_id=None),
                     Score(earned=16, possible=16.0, graded=True, section='hw2', module_id=None)],
        # The dropped scores should be from the assignments that don't exist yet

        'Lab': [Score(earned=1, possible=2.0, graded=True, section='lab1', module_id=None),  # Dropped
                Score(earned=1, possible=1.0, graded=True, section='lab2', module_id=None),
                Score(earned=1, possible=1.0, graded=True, section='lab3', module_id=None),
                Score(earned=5, possible=25.0, graded=True, section='lab4', module_id=None),  # Dropped
                Score(earned=3, possible=4.0, graded=True, section='lab5', module_id=None),  # Dropped
                Score(earned=6, possible=7.0, graded=True, section='lab6', module_id=None),
                Score(earned=5, possible=6.0, graded=True, section='lab7', module_id=None)],

        'Midterm': [Score(earned=50.5, possible=100, graded=True, section="Midterm Exam", module_id=None), ],
    }

    def test_single_section_grader(self):
        midterm_grader = graders.SingleSectionGrader("Midterm", "Midterm Exam")
        lab4_grader = graders.SingleSectionGrader("Lab", "lab4")
        bad_lab_grader = graders.SingleSectionGrader("Lab", "lab42")

        for graded in [midterm_grader.grade(self.empty_gradesheet),
                       midterm_grader.grade(self.incomplete_gradesheet),
                       bad_lab_grader.grade(self.test_gradesheet)]:
            self.assertEqual(len(graded['section_breakdown']), 1)
            self.assertEqual(graded['percent'], 0.0)

        graded = midterm_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.505)
        self.assertEqual(len(graded['section_breakdown']), 1)

        graded = lab4_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2)
        self.assertEqual(len(graded['section_breakdown']), 1)

    def test_assignment_format_grader(self):
        homework_grader = graders.AssignmentFormatGrader("Homework", 12, 2)
        no_drop_grader = graders.AssignmentFormatGrader("Homework", 12, 0)
        # Even though the minimum number is 3, this should grade correctly when 7 assignments are found
        overflow_grader = graders.AssignmentFormatGrader("Lab", 3, 2)
        lab_grader = graders.AssignmentFormatGrader("Lab", 7, 3)

        # Test the grading of an empty gradesheet
        for graded in [homework_grader.grade(self.empty_gradesheet),
                       no_drop_grader.grade(self.empty_gradesheet),
                       homework_grader.grade(self.incomplete_gradesheet),
                       no_drop_grader.grade(self.incomplete_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            # Make sure the breakdown includes 12 sections, plus one summary
            self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = homework_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)  # 100% + 10% / 10 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = no_drop_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0916666666666666)  # 100% + 10% / 12 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = overflow_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.8880952380952382)  # 100% + 10% / 5 assignments
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

        graded = lab_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.9226190476190477)
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

    def test_assignment_format_grader_on_single_section_entry(self):
        midterm_grader = graders.AssignmentFormatGrader("Midterm", 1, 0)
        # Test the grading on a section with one item:
        for graded in [midterm_grader.grade(self.empty_gradesheet),
                       midterm_grader.grade(self.incomplete_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            # Make sure the breakdown includes just the one summary
            self.assertEqual(len(graded['section_breakdown']), 0 + 1)
            self.assertEqual(graded['section_breakdown'][0]['label'], 'Midterm')

        graded = midterm_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.505)
        self.assertEqual(len(graded['section_breakdown']), 0 + 1)

    def test_weighted_subsections_grader(self):
        # First, a few sub graders
        homework_grader = graders.AssignmentFormatGrader("Homework", 12, 2)
        lab_grader = graders.AssignmentFormatGrader("Lab", 7, 3)
        # phasing out the use of SingleSectionGraders, and instead using AssignmentFormatGraders that
        # will act like SingleSectionGraders on single sections.
        midterm_grader = graders.AssignmentFormatGrader("Midterm", 1, 0)

        weighted_grader = graders.WeightedSubsectionsGrader([(homework_grader, homework_grader.category, 0.25),
                                                             (lab_grader, lab_grader.category, 0.25),
                                                             (midterm_grader, midterm_grader.category, 0.5)])

        over_one_weights_grader = graders.WeightedSubsectionsGrader([(homework_grader, homework_grader.category, 0.5),
                                                                     (lab_grader, lab_grader.category, 0.5),
                                                                     (midterm_grader, midterm_grader.category, 0.5)])

        # The midterm should have all weight on this one
        zero_weights_grader = graders.WeightedSubsectionsGrader([(homework_grader, homework_grader.category, 0.0),
                                                                 (lab_grader, lab_grader.category, 0.0),
                                                                 (midterm_grader, midterm_grader.category, 0.5)])

        # This should always have a final percent of zero
        all_zero_weights_grader = graders.WeightedSubsectionsGrader([(homework_grader, homework_grader.category, 0.0),
                                                                     (lab_grader, lab_grader.category, 0.0),
                                                                     (midterm_grader, midterm_grader.category, 0.0)])

        empty_grader = graders.WeightedSubsectionsGrader([])

        graded = weighted_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = over_one_weights_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.7688095238095238)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = zero_weights_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2525)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = all_zero_weights_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        for graded in [weighted_grader.grade(self.empty_gradesheet),
                       weighted_grader.grade(self.incomplete_gradesheet),
                       zero_weights_grader.grade(self.empty_gradesheet),
                       all_zero_weights_grader.grade(self.empty_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
            self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = empty_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

    def test_grader_from_conf(self):

        # Confs always produce a graders.WeightedSubsectionsGrader, so we test this by repeating the test
        # in test_graders.WeightedSubsectionsGrader, but generate the graders with confs.

        weighted_grader = graders.grader_from_conf([
            {
                'type': "Homework",
                'min_count': 12,
                'drop_count': 2,
                'short_label': "HW",
                'weight': 0.25,
            },
            {
                'type': "Lab",
                'min_count': 7,
                'drop_count': 3,
                'category': "Labs",
                'weight': 0.25
            },
            {
                'type': "Midterm",
                'name': "Midterm Exam",
                'short_label': "Midterm",
                'weight': 0.5,
            },
        ])

        empty_grader = graders.grader_from_conf([])

        graded = weighted_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = empty_grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

        # Test that graders can also be used instead of lists of dictionaries
        homework_grader = graders.AssignmentFormatGrader("Homework", 12, 2)
        homework_grader2 = graders.grader_from_conf(homework_grader)

        graded = homework_grader2.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        # TODO: How do we test failure cases? The parser only logs an error when
        # it can't parse something. Maybe it should throw exceptions?
