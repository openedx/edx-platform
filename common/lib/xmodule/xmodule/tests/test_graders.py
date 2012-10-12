"""Grading tests"""
import unittest

from xmodule import graders
from xmodule.graders import Score, aggregate_scores

class GradesheetTest(unittest.TestCase):

    def test_weighted_grading(self):
        scores = []
        Score.__sub__ = lambda me, other: (me.earned - other.earned) + (me.possible - other.possible)

        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=0, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, graded=True, section="summary"))

        scores.append(Score(earned=0, possible=5, graded=False, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertEqual(all, Score(earned=0, possible=5, graded=False, section="summary"))
        self.assertEqual(graded, Score(earned=0, possible=0, graded=True, section="summary"))

        scores.append(Score(earned=3, possible=5, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=3, possible=10, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=3, possible=5, graded=True, section="summary"))

        scores.append(Score(earned=2, possible=5, graded=True, section="summary"))
        all, graded = aggregate_scores(scores)
        self.assertAlmostEqual(all, Score(earned=5, possible=15, graded=False, section="summary"))
        self.assertAlmostEqual(graded, Score(earned=5, possible=10, graded=True, section="summary"))


class GraderTest(unittest.TestCase):

    empty_gradesheet = {
    }

    incomplete_gradesheet = {
        'Homework': [],
        'Lab': [],
        'Midterm': [],
    }

    test_gradesheet = {
        'Homework': [Score(earned=2, possible=20.0, graded=True, section='hw1'),
              Score(earned=16, possible=16.0, graded=True, section='hw2')],
              #The dropped scores should be from the assignments that don't exist yet

        'Lab': [Score(earned=1, possible=2.0, graded=True, section='lab1'),  # Dropped
             Score(earned=1, possible=1.0, graded=True, section='lab2'),
             Score(earned=1, possible=1.0, graded=True, section='lab3'),
             Score(earned=5, possible=25.0, graded=True, section='lab4'),  # Dropped
             Score(earned=3, possible=4.0, graded=True, section='lab5'),  # Dropped
             Score(earned=6, possible=7.0, graded=True, section='lab6'),
             Score(earned=5, possible=6.0, graded=True, section='lab7')],

        'Midterm': [Score(earned=50.5, possible=100, graded=True, section="Midterm Exam"), ],
    }

    def test_SingleSectionGrader(self):
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")
        lab4Grader = graders.SingleSectionGrader("Lab", "lab4")
        badLabGrader = graders.SingleSectionGrader("Lab", "lab42")

        for graded in [midtermGrader.grade(self.empty_gradesheet),
                        midtermGrader.grade(self.incomplete_gradesheet),
                        badLabGrader.grade(self.test_gradesheet)]:
            self.assertEqual(len(graded['section_breakdown']), 1)
            self.assertEqual(graded['percent'], 0.0)

        graded = midtermGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.505)
        self.assertEqual(len(graded['section_breakdown']), 1)

        graded = lab4Grader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2)
        self.assertEqual(len(graded['section_breakdown']), 1)

    def test_AssignmentFormatGrader(self):
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        noDropGrader = graders.AssignmentFormatGrader("Homework", 12, 0)
        #Even though the minimum number is 3, this should grade correctly when 7 assignments are found
        overflowGrader = graders.AssignmentFormatGrader("Lab", 3, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)

        #Test the grading of an empty gradesheet
        for graded in [homeworkGrader.grade(self.empty_gradesheet),
                        noDropGrader.grade(self.empty_gradesheet),
                        homeworkGrader.grade(self.incomplete_gradesheet),
                        noDropGrader.grade(self.incomplete_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            #Make sure the breakdown includes 12 sections, plus one summary
            self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = homeworkGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)  # 100% + 10% / 10 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = noDropGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0916666666666666)  # 100% + 10% / 12 assignments
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        graded = overflowGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.8880952380952382)  # 100% + 10% / 5 assignments
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

        graded = labGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.9226190476190477)
        self.assertEqual(len(graded['section_breakdown']), 7 + 1)

    def test_WeightedSubsectionsGrader(self):
        #First, a few sub graders
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")

        weightedGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.25),
                                                            (labGrader, labGrader.category, 0.25),
        (midtermGrader, midtermGrader.category, 0.5)])

        overOneWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.5),
                                                                  (labGrader, labGrader.category, 0.5),
        (midtermGrader, midtermGrader.category, 0.5)])

        #The midterm should have all weight on this one
        zeroWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.0),
                                                               (labGrader, labGrader.category, 0.0),
        (midtermGrader, midtermGrader.category, 0.5)])

        #This should always have a final percent of zero
        allZeroWeightsGrader = graders.WeightedSubsectionsGrader([(homeworkGrader, homeworkGrader.category, 0.0),
                                                                  (labGrader, labGrader.category, 0.0),
        (midtermGrader, midtermGrader.category, 0.0)])

        emptyGrader = graders.WeightedSubsectionsGrader([])

        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = overOneWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.7688095238095238)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = zeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.2525)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = allZeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        for graded in [weightedGrader.grade(self.empty_gradesheet),
                        weightedGrader.grade(self.incomplete_gradesheet),
                        zeroWeightsGrader.grade(self.empty_gradesheet),
                        allZeroWeightsGrader.grade(self.empty_gradesheet)]:
            self.assertAlmostEqual(graded['percent'], 0.0)
            self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
            self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

    def test_graderFromConf(self):

        #Confs always produce a graders.WeightedSubsectionsGrader, so we test this by repeating the test
        #in test_graders.WeightedSubsectionsGrader, but generate the graders with confs.

        weightedGrader = graders.grader_from_conf([
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

        emptyGrader = graders.grader_from_conf([])

        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.5106547619047619)
        self.assertEqual(len(graded['section_breakdown']), (12 + 1) + (7 + 1) + 1)
        self.assertEqual(len(graded['grade_breakdown']), 3)

        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.0)
        self.assertEqual(len(graded['section_breakdown']), 0)
        self.assertEqual(len(graded['grade_breakdown']), 0)

        #Test that graders can also be used instead of lists of dictionaries
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        homeworkGrader2 = graders.grader_from_conf(homeworkGrader)

        graded = homeworkGrader2.grade(self.test_gradesheet)
        self.assertAlmostEqual(graded['percent'], 0.11)
        self.assertEqual(len(graded['section_breakdown']), 12 + 1)

        #TODO: How do we test failure cases? The parser only logs an error when
        #it can't parse something. Maybe it should throw exceptions?

