"""
Unit tests for instructor dashboard

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

./manage.py lms --settings test test lms/djangoapps/instructor
"""
import json

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory, AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from courseware.tests.factories import OfflineComputedGradeFactory
from xmodule.modulestore.django import modulestore

from instructor_task.tests.factories import InstructorTaskFactory

USER_COUNT = 11


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorDashboardGradeDownloadCSV(ModuleStoreTestCase):
    grading_policy = None

    def setUp(self):
        # create an instructor, and log them in:
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password='test')

        # create a dummy course in Mongo:
        modulestore().request_cache = modulestore().metadata_inheritance_cache_subsystem = None
        self.course = CourseFactory.create()

        # create users that are enrolled in the course:
        self.users = [UserFactory() for _ in xrange(USER_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
            # create grade entries in the OfflineTable
            gradeset = {"grade": None,
                        "totaled_scores": {
                            "Foldit": [[0, 1, True, "Foldit Progress"]],
                            "Problem Set": [[0.0, 100.0, True, "Problem Set 1: Chemistry and Macromolecules"],
                                            [0.0, 105.0, True, "Problem Set 2: Proteins, Enzymes, and Pathways"],
                                            [0.0, 100.0, True, "Problem Set 3: Genetics"],
                                            [13.75, 100.0, True, "Problem Set 4: Molecular Biology"],
                                            [0.0, 100.0, True, "Problem Set 5: Recombinant DNA"]],
                            "Practice Problem Set": [[0.0, 100.0, True, "Practice Problem Set: Genetics II"]],
                            "Midterm": [[0.0, 109.0, True, "Exam 1"]]
                         },
                        "percent": 0.0,
                        "raw_scores": [[0, 1, True, "FoldIt challenge"], [0.0, 5.0, True, "Part IV"], [0.0, 10.0, True, "Part III"],
                                       [0.0, 10.0, True, "Part II"], [0.0, 10.0, True, "Problem 7: Edit a Molecule, Part I"],
                                       [0.0, 10.0, True, "Problem 6: Molecules and Membranes"],
                                       [0.0, 20.0, True, "Problem 5: Functional Groups"],
                                       [0.0, 5.0, True, "Problem 4: Read a Molecule, Part II"],
                                       [0.0, 10.0, True, "Read a Molecule, Part I"],
                                       [0.0, 5.0, True, "Problem 3: Hydrogen Bonds"],
                                       [0.0, 5.0, True, "Problem 2: Bond Polarity"],
                                       [0.0, 10.0, True, "Problem 1: Covalent Bonds"],
                                       [0.0, 5.0, True, "Biochemical Pathways, Part G"], [0.0, 5.0, True, "Biochemical Pathways, Part F"], [0.0, 5.0, True, "Biochemical Pathways, Part E"], [0.0, 5.0, True, "Biochemical Pathways, Part D"], [0.0, 5.0, True, "Biochemical Pathways, Part C"], [0.0, 5.0, True, "Biochemical Pathways, Part B"], [0.0, 5.0, True, "Biochemical Pathways, Part A"], [0.0, 5.0, True, "Enzymes"], [0.0, 5.0, True, "Proteins and Membranes, Part C"], [0.0, 5.0, True, "Proteins and Membranes, Part B"], [0.0, 5.0, True, "Proteins and Membranes, Part A"], [0.0, 5.0, True, "Designing Proteins in Two Dimensions, Part IV"], [0.0, 8.0, True, "Designing Proteins in Two Dimensions, Part III"], [0.0, 6.0, True, "Designing Proteins in Two Dimensions, Part II"], [0.0, 6.0, True, "Designing Proteins in Two Dimensions, Part I"], [0.0, 5.0, True, "Explore a Protein, Part E"], [0.0, 5.0, True, "Explore a Protein, Part D"], [0.0, 5.0, True, "Explore a Protein, Part C"], [0.0, 5.0, True, "Explore a Protein, Part B"], [0.0, 5.0, True, "Explore a Protein, Part A"], [0.0, 10.0, True, "Problem 17, VGL 6: Two Genes and Linkage"], [0.0, 10.0, True, "Problem 16, VGL 5: Two Genes and Simple Dominance"], [0.0, 4.0, True, "Problem 15, VGL 4: Sex Linkage II"], [0.0, 4.0, True, "Problem 14, VGL 3: Sex Linkage"], [0.0, 3.0, True, "Problem 13, VGL 2: Incomplete Dominance"], [0.0, 3.0, True, "Problem 12, VGL 1: Simple Dominance"], [0.0, 6.0, True, "Problem 11, Recombination Maps"], [0.0, 6.0, True, "Problem 10, Flies II"], [0.0, 6.0, True, "Problem 09b, Flies, Part B"], [0.0, 6.0, True, "Problem 09a, Flies, Part A"], [0.0, 6.0, True, "Problem 08, Peas IV"], [0.0, 9.0, True, "Problem 07, Peas III"], [0.0, 6.0, True, "Problem 06, Rats IV"], [0.0, 3.0, True, "Problem 05, Rats III"], [0.0, 6.0, True, "Problem 04, Peas II"], [0.0, 6.0, True, "Problem 03, Peas I"], [0.0, 3.0, True, "Problem 02, Rats II"], [0.0, 3.0, True, "Problem 01, Rats I"], [0.0, 5.0, True, "Edit a Gene Part E"], [0.0, 5.0, True, "Edit a Gene Part D"], [0.0, 5.0, True, "Edit a Gene Part C"], [0.0, 5.0, True, "Edit a Gene Part B"], [0.0, 5.0, True, "Edit a Gene Part A"], [0.0, 10.0, True, "Explore A Gene, Part E"], [0.0, 10.0, True, "Explore A Gene, Part D"], [0.0, 10.0, True, "Explore A Gene, Part C"], [0.0, 5.0, True, "Explore A Gene, Part B"], [0.0, 5.0, True, "Explore A Gene, Part A"], [2.5, 5.0, True, "A Small Gene, Part E"], [0.0, 5.0, True, "A Small Gene, Part D"], [2.5, 5.0, True, "A Small Gene, Part C"], [2.5, 5.0, True, "A Small Gene, Part B"], [0.0, 5.0, True, "A Small Gene, Part A"], [3.75, 5.0, True, "DNA Replication"], [2.5, 5.0, True, "Chargaff\u2019s Ratios"], [0.0, 10.0, True, "Problem 08, Task 4: Create a translational fusion protein"], [0.0, 10.0, True, "Problem 07, Build a Plasmid, Part C"], [0.0, 10.0, True, "Problem 07, Build a Plasmid, Part B"], [0.0, 10.0, True, "Problem 07, Build a Plasmid, Part A"], [0.0, 10.0, True, "Problem 06, DNA Sequencing"], [0.0, 10.0, True, "Problem 05, Genotyping Using PCR and Restriction Enzymes, Part B"], [0.0, 10.0, True, "Problem 05, Genotyping Using PCR and Restriction Enzymes, Part A"], [0.0, 5.0, True, "Problem 04, Plasmids"], [0.0, 10.0, True, "Problem 03, Polymerase Chain Reaction (PCR)"], [0.0, 5.0, True, "Problem 02, DNA Electrophoresis, Part B"], [0.0, 5.0, True, "Problem 02, DNA Electrophoresis, Part A"], [0.0, 5.0, True, "Problem 01, Restriction Enzymes"], [0.0, 10.0, True, "Population Genetics"], [0.0, 5.0, True, "Biochemical Genetics, Part 2"], [0.0, 5.0, True, "Biochemical Genetics, Part 1"], [0.0, 10.0, True, "Pedigrees II, Part D"], [0.0, 10.0, True, "Pedigrees II, Part C"], [0.0, 10.0, True, "Pedigrees II, Part B"], [0.0, 10.0, True, "Pedigrees II, Part A"], [0.0, 10.0, True, "Pedigrees I, Part D"], [0.0, 10.0, True, "Pedigrees I, Part C"], [0.0, 10.0, True, "Pedigrees I, Part B"], [0.0, 10.0, True, "Pedigrees I, Part A"], [0.0, 7.0, True, "Problem 07, Chicken Genetics, Part D"], [0.0, 7.0, True, "Problem 07, Chicken Genetics, Part C"], [0.0, 5.0, True, "Problem 07, Chicken Genetics, Part B"], [0.0, 5.0, True, "Problem 07, Chicken Genetics, Part A"], [0.0, 7.0, True, "Problem 06, Pedigrees II"], [0.0, 7.0, True, "Problem 05, Pedigrees, Part D"], [0.0, 7.0, True, "Problem 05, Pedigrees, Part C"], [0.0, 7.0, True, "Problem 05, Pedigrees, Part B"], [0.0, 7.0, True, "Problem 05, Pedigrees, Part A"], [0.0, 5.0, True, "Problem 04, Pathways, Part C"], [0.0, 5.0, True, "Problem 04, Pathways, Part B"], [0.0, 5.0, True, "Problem 04, Pathways, Part A"], [0.0, 5.0, True, "Problem 03, Free Energy"], [0.0, 5.0, True, "Problem 02, Explore a Protein, Part C"], [0.0, 5.0, True, "Problem 02, Explore a Protein, Part B"], [0.0, 5.0, True, "Problem 02, Explore a Protein, Part A"], [0.0, 5.0, True, "Problem 01, Edit a Molecule, Part C"], [0.0, 5.0, True, "Problem 01, Edit a Molecule, Part B"], [0.0, 5.0, True, "Problem 01, Edit a Molecule, Part A"]],
                        "section_breakdown": [{"category": "Problem Set", "percent": 0.0, "detail": "Problem Set 1 - Problem Set 1: Chemistry and Macromolecules - 0% (0/100)", "label": "PSet 01"},
                                              {"category": "Problem Set", "percent": 0.0, "detail": "Problem Set 2 - Problem Set 2: Proteins, Enzymes, and Pathways - 0% (0/105)", "label": "PSet 02"},
                                              {"category": "Problem Set", "percent": 0.0, "detail": "Problem Set 3 - Problem Set 3: Genetics - 0% (0/100)", "label": "PSet 03"},
                                              {"category": "Problem Set", "percent": 0.1375, "detail": "Problem Set 4 - Problem Set 4: Molecular Biology - 14% (13.8/100)", "label": "PSet 04"},
                                              {"category": "Problem Set", "percent": 0.0, "detail": "Problem Set 5 - Problem Set 5: Recombinant DNA - 0% (0/100)", "label": "PSet 05"},
                                              {"category": "Problem Set", "percent": 0, "detail": "Problem Set 6 Unreleased - 0% (?/?)", "label": "PSet 06"},
                                              {"category": "Problem Set", "prominent": True, "percent": 0.02291666666666667, "detail": "Problem Set Average = 2%", "label": "PSet Avg"},
                                              {"category": "Practice Problem Set: Genetics II", "prominent": True, "percent": 0.0, "detail": "Practice Problem Set: Genetics II - 0% (0/100)", "label": "Practice PSet"},
                                              {"category": "Foldit Progress", "prominent": True, "percent": 0.0, "detail": "Foldit Progress - 0% (0/1)", "label": "Foldit"},
                                              {"category": "Midterm", "percent": 0.0, "detail": "Midterm 1 - Exam 1 - 0% (0/109)", "label": "Midterm 01"},
                                              {"category": "Midterm", "percent": 0, "detail": "Midterm 2 Unreleased - 0% (?/?)", "label": "Midterm 02"},
                                              {"category": "Midterm", "prominent": True, "percent": 0.0, "detail": "Midterm Average = 0%", "label": "Midterm Avg"},
                                              {"category": "Final Exam", "prominent": True, "percent": 0.0, "detail": "Final Exam - 0% (?/?)", "label": "Final"}],
                        "grade_breakdown": [{"category": "Problem Set", "percent": 0.003930208333333334, "detail": "Problem Set = 0.4% of a possible 17%"},
                                            {"category": "Practice Problem Set: Genetics II", "percent": 0.0, "detail": "Practice Problem Set: Genetics II = 0.0% of a possible 0%"},
                                            {"category": "Foldit Progress", "percent": 0.0, "detail": "Foldit Progress = 0.0% of a possible 3%"},
                                            {"category": "Midterm", "percent": 0.0, "detail": "Midterm = 0.0% of a possible 50%"},
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     {"category": "Final Exam", "percent": 0.0, "detail": "Final Exam = 0.0% of a possible 30%"}]
                        }

            gradeset_json = json.dumps(gradeset)
            OfflineComputedGradeFactory.create(user=user, course_id=self.course.id, gradeset=gradeset_json)

        # create an entry in InstructorTask to indicate that grades have already been calculated
        self.task = InstructorTaskFactory.create(
            task_type='update_offline_grades',
            course_id=self.course.id,
            task_state='SUCCESS',
            task_key='',
            task_id="dummy_id"
        )

    def test_download_grades_csv(self):
        course = self.course
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        msg = "url = {0}\n".format(url)
        response = self.client.post(url, {'action': 'Download CSV of all student grades for this course'})
        msg += "instructor dashboard download csv grades: response = '{0}'\n".format(response)

        self.assertEqual(response['Content-Type'], 'text/csv', msg)

        cdisp = response['Content-Disposition']
        msg += "Content-Disposition = '%s'\n" % cdisp
        self.assertEqual(cdisp, 'attachment; filename=grades_{0}.csv'.format(course.id), msg)

        body = response.content.replace('\r', '')

        # All the not-actually-in-the-course hw and labs come from the
        # default grading policy string in graders.py
#         expected_body = '''"ID","Username","Full Name","edX email","External email","Updated","HW 01","HW 02","HW 03","HW 04","HW 05","HW 06","HW 07","HW 08","HW 09","HW 10","HW 11","HW 12","HW Avg","Lab 01","Lab 02","Lab 03","Lab 04","Lab 05","Lab 06","Lab 07","Lab 08","Lab 09","Lab 10","Lab 11","Lab 12","Lab Avg","Midterm","Final"
# "2","u2","Username","view2@test.com","","updated-goes-here","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0"
# '''
#         expected_body =  ''"ID","Username","Full Name","edX email","External email","Updated","PSet 01","PSet 02","PSet 03","PSet 04","PSet 05","PSet 06","PSet Avg","Practice PSet","Foldit","Midterm 01","Midterm 02","Midterm Avg","Final"
# "2","robot45","Robot Test","robot+test+45@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
# "3","robot46","Robot Test","robot+test+46@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
# "4","robot47","Robot Test","robot+test+47@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
# "5","robot48","Robot Test","robot+test+48@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
# "6","robot49","Robot Test","robot+test+49@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
# "7","robot50","Robot Test","robot+test+50@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
#         "8","robot51","Robot Test","robot+test+51@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
#         "9","robot52","Robot Test","robot+test+52@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
#         "10","robot53","Robot Test","robot+test+53@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
#         "11","robot54","Robot Test","robot+test+54@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"
#         "12","robot55","Robot Test","robot+test+55@edx.org","","updated-goes-here","0.0","0.0","0.0","0.1375","0.0","0","0.0229166666667","0.0","0.0","0.0","0","0.0","0.0"'''
#         self.assertEqual(body, expected_body)
