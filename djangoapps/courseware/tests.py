import unittest

import numpy

import courseware.modules
import courseware.capa.calc as calc
import courseware.graders as graders
from courseware.graders import Score, CourseGrader, WeightedSubsectionsGrader, SingleSectionGrader, AssignmentFormatGrader
from courseware.grades import aggregate_scores

class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_module_class(self):
        vc = courseware.modules.get_module_class('video')
        vc_str = "<class 'courseware.modules.video_module.Module'>"
        self.assertEqual(str(vc), vc_str)
        video_id = courseware.modules.get_default_ids()['video']
        self.assertEqual(video_id, 'youtube')

    def test_calc(self):
        variables={'R1':2.0, 'R3':4.0}
        functions={'sin':numpy.sin, 'cos':numpy.cos}

        self.assertTrue(abs(calc.evaluator(variables, functions, "10000||sin(7+5)+0.5356"))<0.01)
        self.assertEqual(calc.evaluator({'R1': 2.0, 'R3':4.0}, {}, "13"), 13)
        self.assertEqual(calc.evaluator(variables, functions, "13"), 13)
        self.assertEqual(calc.evaluator({'a': 2.2997471478310274, 'k': 9, 'm': 8, 'x': 0.66009498411213041}, {}, "5"), 5)
        self.assertEqual(calc.evaluator({},{}, "-1"), -1)
        self.assertEqual(calc.evaluator({},{}, "-0.33"), -.33)
        self.assertEqual(calc.evaluator({},{}, "-.33"), -.33)
        self.assertEqual(calc.evaluator(variables, functions, "R1*R3"), 8.0)
        self.assertTrue(abs(calc.evaluator(variables, functions, "sin(e)-0.41"))<0.01)
        self.assertTrue(abs(calc.evaluator(variables, functions, "k*T/q-0.025"))<0.001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "e^(j*pi)")+1)<0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "j||1")-0.5-0.5j)<0.00001)
        variables['t'] = 1.0
        self.assertTrue(abs(calc.evaluator(variables, functions, "t")-1.0)<0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T")-1.0)<0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "t", cs=True)-1.0)<0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T", cs=True)-298)<0.2)
        exception_happened = False
        try: 
            calc.evaluator({},{}, "5+7 QWSEKO")
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

        try: 
            calc.evaluator({'r1':5},{}, "r1+r2")
        except calc.UndefinedVariable:
            pass
        
        self.assertEqual(calc.evaluator(variables, functions, "r1*r3"), 8.0)

        exception_happened = False
        try: 
            calc.evaluator(variables, functions, "r1*r3", cs=True)
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

class GradesheetTest(unittest.TestCase):

    def test_weighted_grading(self):
        scores = []
        Score.__sub__=lambda me, other: (me.earned - other.earned) + (me.possible - other.possible)

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
        'Midterm' : [],
    }
        
    test_gradesheet = {
        'Homework': [Score(earned=2, possible=20.0, graded=True, section='hw1'),
              Score(earned=16, possible=16.0, graded=True, section='hw2')],
              #The dropped scores should be from the assignments that don't exist yet
              
        'Lab': [Score(earned=1, possible=2.0, graded=True, section='lab1'), #Dropped
             Score(earned=1, possible=1.0, graded=True, section='lab2'),
             Score(earned=1, possible=1.0, graded=True, section='lab3'),
             Score(earned=5, possible=25.0, graded=True, section='lab4'), #Dropped
             Score(earned=3, possible=4.0, graded=True, section='lab5'), #Dropped
             Score(earned=6, possible=7.0, graded=True, section='lab6'),
             Score(earned=5, possible=6.0, graded=True, section='lab7')],
        
        'Midterm' : [Score(earned=50.5, possible=100, graded=True, section="Midterm Exam"),],
    }
    
    def test_SingleSectionGrader(self):
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")
        lab4Grader = graders.SingleSectionGrader("Lab", "lab4")
        badLabGrader = graders.SingleSectionGrader("Lab", "lab42")
        
        for graded in [midtermGrader.grade(self.empty_gradesheet), 
                        midtermGrader.grade(self.incomplete_gradesheet), 
                        badLabGrader.grade(self.test_gradesheet)]:
            self.assertEqual( len(graded['section_breakdown']), 1 )
            self.assertEqual( graded['percent'], 0.0 )
        
        graded = midtermGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.505 )
        self.assertEqual( len(graded['section_breakdown']), 1 )
        
        graded = lab4Grader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.2 )
        self.assertEqual( len(graded['section_breakdown']), 1 )
        
    def test_AssignmentFormatGrader(self):
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        noDropGrader = graders.AssignmentFormatGrader("Homework", 12, 0)
        #Even though the minimum number is 3, this should grade correctly when 7 assignments are found
        overflowGrader = graders.AssignmentFormatGrader("Lab", 3, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)
        
        
        #Test the grading of an empty gradesheet
        for graded in [ homeworkGrader.grade(self.empty_gradesheet), 
                        noDropGrader.grade(self.empty_gradesheet),
                        homeworkGrader.grade(self.incomplete_gradesheet),
                        noDropGrader.grade(self.incomplete_gradesheet) ]:
            self.assertAlmostEqual( graded['percent'], 0.0 )
            #Make sure the breakdown includes 12 sections, plus one summary
            self.assertEqual( len(graded['section_breakdown']), 12 + 1 )
        
        
        graded = homeworkGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.11 ) # 100% + 10% / 10 assignments
        self.assertEqual( len(graded['section_breakdown']), 12 + 1 )
        
        graded = noDropGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.0916666666666666 ) # 100% + 10% / 12 assignments
        self.assertEqual( len(graded['section_breakdown']), 12 + 1 )
        
        graded = overflowGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.8880952380952382 ) # 100% + 10% / 5 assignments
        self.assertEqual( len(graded['section_breakdown']), 7 + 1 )
        
        graded = labGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.9226190476190477 )
        self.assertEqual( len(graded['section_breakdown']), 7 + 1 )
        
        
    def test_WeightedSubsectionsGrader(self):
        #First, a few sub graders
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        labGrader = graders.AssignmentFormatGrader("Lab", 7, 3)
        midtermGrader = graders.SingleSectionGrader("Midterm", "Midterm Exam")
        
        weightedGrader = graders.WeightedSubsectionsGrader( [(homeworkGrader, homeworkGrader.category, 0.25), (labGrader, labGrader.category, 0.25), 
        (midtermGrader, midtermGrader.category, 0.5)] )
        
        overOneWeightsGrader = graders.WeightedSubsectionsGrader( [(homeworkGrader, homeworkGrader.category, 0.5), (labGrader, labGrader.category, 0.5), 
        (midtermGrader, midtermGrader.category, 0.5)] )
        
        #The midterm should have all weight on this one
        zeroWeightsGrader = graders.WeightedSubsectionsGrader( [(homeworkGrader, homeworkGrader.category, 0.0), (labGrader, labGrader.category, 0.0), 
        (midtermGrader, midtermGrader.category, 0.5)] )
        
        #This should always have a final percent of zero
        allZeroWeightsGrader = graders.WeightedSubsectionsGrader( [(homeworkGrader, homeworkGrader.category, 0.0), (labGrader, labGrader.category, 0.0), 
        (midtermGrader, midtermGrader.category, 0.0)] )
        
        emptyGrader = graders.WeightedSubsectionsGrader( [] )
        
        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.5106547619047619 )
        self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
        self.assertEqual( len(graded['grade_breakdown']), 3 )
        
        graded = overOneWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.7688095238095238 )
        self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
        self.assertEqual( len(graded['grade_breakdown']), 3 )
        
        graded = zeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.2525 )
        self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
        self.assertEqual( len(graded['grade_breakdown']), 3 )
        
        
        graded = allZeroWeightsGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.0 )
        self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
        self.assertEqual( len(graded['grade_breakdown']), 3 )
        
        for graded in [ weightedGrader.grade(self.empty_gradesheet), 
                        weightedGrader.grade(self.incomplete_gradesheet),
                        zeroWeightsGrader.grade(self.empty_gradesheet),
                        allZeroWeightsGrader.grade(self.empty_gradesheet)]:
            self.assertAlmostEqual( graded['percent'], 0.0 )
            self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
            self.assertEqual( len(graded['grade_breakdown']), 3 )
            
            
        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.0 )
        self.assertEqual( len(graded['section_breakdown']), 0 )
        self.assertEqual( len(graded['grade_breakdown']), 0 )
        
    

    def test_graderFromConf(self):
        
        #Confs always produce a graders.WeightedSubsectionsGrader, so we test this by repeating the test
        #in test_graders.WeightedSubsectionsGrader, but generate the graders with confs.
        
        weightedGrader = graders.grader_from_conf([
            {
                'type' : "Homework",
                'min_count' : 12,
                'drop_count' : 2,
                'short_label' : "HW",
                'weight' : 0.25,
            },
            {
                'type' : "Lab",
                'min_count' : 7,
                'drop_count' : 3,
                'category' : "Labs",
                'weight' : 0.25
            },
            {
                'type' : "Midterm",
                'name' : "Midterm Exam",
                'short_label' : "Midterm",
                'weight' : 0.5,
            },
        ])
        
        emptyGrader = graders.grader_from_conf([])
        
        graded = weightedGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.5106547619047619 )
        self.assertEqual( len(graded['section_breakdown']), (12 + 1) + (7+1) + 1 )
        self.assertEqual( len(graded['grade_breakdown']), 3 )
        
        graded = emptyGrader.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.0 )
        self.assertEqual( len(graded['section_breakdown']), 0 )
        self.assertEqual( len(graded['grade_breakdown']), 0 )
        
        #Test that graders can also be used instead of lists of dictionaries
        homeworkGrader = graders.AssignmentFormatGrader("Homework", 12, 2)
        homeworkGrader2 = graders.grader_from_conf(homeworkGrader)
        
        graded = homeworkGrader2.grade(self.test_gradesheet)
        self.assertAlmostEqual( graded['percent'], 0.11 )
        self.assertEqual( len(graded['section_breakdown']), 12 + 1 )
        
        #TODO: How do we test failure cases? The parser only logs an error when it can't parse something. Maybe it should throw exceptions?

