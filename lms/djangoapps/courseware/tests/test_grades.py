"""
This is the start of a test for grades.
It is very incomplete - we're only testing one function
right now.
"""
from mock import MagicMock

import unittest
import courseware.grades as grades
import courseware.module_render as module_render
from courseware.model_data import LmsKeyValueStore

from xmodule.graders import Score


class FakeChildFactory(object):
    """
    Makes fake child descriptors.
    """
    @classmethod
    def create(cls, name):
        """
        Creates a new fake child with the given name.
        """
        out = MagicMock()
        out.has_dynamic_children = lambda: False
        out.get_children = lambda: []
        out.name = name
        return out


class TestGrades(unittest.TestCase):
    """
    Test the grader.
    """

    def test_yield_dynamic_descriptor_descendents(self):
        """
        Make sure that yield_dynamic_descriptor_descendents instantiates
        modules to get children.
        """

        child_a = FakeChildFactory.create('a')
        child_b = FakeChildFactory.create('b')
        child_c = FakeChildFactory.create('c')

        fake_parent = MagicMock()
        fake_parent.has_dynamic_children = lambda: True
        # These are the wrong children.
        fake_parent.get_children = lambda: [child_a, child_b, child_c]

        def fake_module_creator(descriptor):
            """
            A mock of the module creator.  Returns a set of children only
            if called with our fake_parent.
            """
            if descriptor == fake_parent:
                fake_module = MagicMock()
                fake_module.get_child_descriptors = lambda: [child_a, child_b]
                return fake_module
            else:
                return None

        # Test with dynamic children
        dynamic_children = list(grades.yield_dynamic_descriptor_descendents(fake_parent, fake_module_creator))
        self.assertTrue(child_a in dynamic_children)
        self.assertTrue(child_b in dynamic_children)
        self.assertTrue(child_c not in dynamic_children)

        # Test without dynamic children
        fake_parent.has_dynamic_children = lambda: False
        regular_children = list(grades.yield_dynamic_descriptor_descendents(fake_parent, fake_module_creator))
        self.assertTrue(child_a in regular_children)
        self.assertTrue(child_b in regular_children)
        self.assertTrue(child_c in regular_children)

    def test_compute_graded_total(self):
        """
        Tests grading for a single section.
        compute_graded_total(section, student, course_id, m_d_c, request)
        - section['section_descriptor'] returns the descriptor for this section.
        - student needs an id
        - All other paramenters are touched through helper functions only.

        Functions to mock:
        grades.should_grade_section(descriptor, m_d_c, student_id) -> True/False
        .module_render.get_module_for_descriptor(student, request, descriptor, m_d_c, course_id) -> Xmodule
        grades.yield_dynamic_descriptor_descendents(descriptor, create_module) -> iter through descriptors
        grades.get_score(course_id, student, descriptor, create_module, m_d_c) -> (correct, total)
        grades.find_attempted(descriptor, m_d_c, student_id) -> True/False
        """

        section = {'section_descriptor': MagicMock(), 'xmoduledescriptors': MagicMock()}
        student = MagicMock()
        student.id = 'my id'
        course_id = 'course id'
        m_d_c = MagicMock()  # We will never query the mdc directly.
        request = MagicMock()   # Same as above.

        # Monkey patching!
        def fake_should_grade_section(descriptor, m_d_c, student_id):
            """ Always grade :) """
            return True
        grades.find_should_grade_section = fake_should_grade_section

        def fake_get_module_for_descriptor(student, request, descriptor, m_d_c, course_id):
            """Don't even return anything; this output is not directly used."""
            return None
        module_render.get_module_for_descriptor = fake_get_module_for_descriptor

        def fake_yield_dynamic_descriptor_descendents(descriptor, create_module):
            """
            Return a bunch of fake descriptors, in iterator form.  Makes 4 descriptors:
            0: not graded.
            1: graded, but total is 0.
            2, 3: normal
            """
            for i in xrange(4):
                out = MagicMock()
                out.display_name_with_default = str(i)
                out.lms = MagicMock()
                out.lms.graded = False if (i == 0) else True
                yield out
        grades.yield_dynamic_descriptor_descendents = fake_yield_dynamic_descriptor_descendents

        def fake_get_score(course_id, student, descriptor, create_module, m_d_c):
            """
            Returns a score, based on the descriptor passed in.
            0: None / None
            1: 5 / 0
            2: 2 / 4
            3: 0 / 5
            """
            number = int(descriptor.display_name_with_default)
            if number == 0:
                return (None, None)
            elif number == 1:
                return (5, 0)
            elif number == 2:
                return (2, 4)
            elif number == 3:
                return (0, 5)
            else:
                raise Exception('get_score called with unexpected input.')
        grades.get_score = fake_get_score

        def fake_find_attempted(descriptor, m_d_c, student_id):
            """Always return True. """
            return True
        grades.find_attempted = fake_find_attempted

        # Actually do the test.
        graded_total, raw_scores = grades.compute_graded_total(section, student, course_id, m_d_c, request)
        # Reset all of the monkey patching.
        # Do this before assertions, because if an assertion fails, the remaining code is not run.
        reload(grades)
        reload(module_render)

        self.assertTrue(graded_total.earned == 2)
        self.assertTrue(graded_total.possible == 9)
        self.assertTrue(graded_total.graded)

        print len(raw_scores)
        self.assertTrue(len(raw_scores) == 3)

    def test_grade(self):
        """
        Test the grade function.
        grade(student, request, course, model_data_cache=None, keep_raw_scores=False)
        student - not used directly.
        request - not used directly.
        course:
            .grading_context['graded_sections']
            .id
            .grader.grade - return a grade summary
        model_data_cache - not used directly, but can't be None.
        keep_raw_scores - True/False

        Things to mock:
        compute_graded_total(section, student, course_id, m_d_c, request)
        grade_for_percentage(cutoffs, percent_summary)
        """
        student = MagicMock()
        request = MagicMock()
        course = MagicMock()
        course.grading_context = {
            'graded_sections': {
                'HW': ['HW1', 'HW2'],
                'Quiz': ['Quiz1'],
            },
        }
        course.id = 'my id'
        course.grader = MagicMock()

        def fake_grade(totaled_scores, generate_random_scores=False):
            """A fake course.grader.grade"""
            return {
                'percent': 64.5,
            }
        course.grader.grade = fake_grade
        m_d_c = MagicMock()

        def fake_compute_graded_total(section, student, course_id, m_d_c, request):
            """
            A fake compute_graded_total.  Expects a string for section, instead of
            a real section.
            """
            if section == 'HW1':
                return (
                    Score(4.0, 10.0, True, 'HW1', ),  # attempted=True
                    ['RS1']
                )
            elif section == 'HW2':
                return (
                    Score(0.0, 10.0, True, 'HW2', ),  # attempted=False
                    ['RS2']
                )
            elif section == 'Quiz1':
                return (
                    Score(85.0, 100.0, True, 'Quiz1', ),  # attempted=True
                    ['RS3']
                )
        grades.compute_graded_total = fake_compute_graded_total

        def fake_grade_for_percentage(cutoffs, percent_summary):
            """A mock of grade_for_percentage"""
            return 'A'
        grades.grade_for_percentage = fake_grade_for_percentage

        grade_summary = grades.grade(student, request, course, model_data_cache=m_d_c, keep_raw_scores=True)
        reload(grades)

        print grade_summary['totaled_scores']
        self.assertTrue(grade_summary['percent'] == 64.5)
        self.assertTrue('HW' in grade_summary['totaled_scores'])
        self.assertTrue('HW' in grade_summary['totaled_scores'])
        self.assertTrue('Quiz' in grade_summary['totaled_scores'])
        self.assertTrue(grade_summary['raw_scores'] == ['RS1', 'RS2', 'RS3'])
        self.assertTrue(grade_summary['grade'] == 'A')



class TestFindShouldGradeSection(unittest.TestCase):
    """
    Test find_should_grade_section.

    find_should_grade_section should:
        return True when at least one problem in the section has been seen in cache
        return True when a module's grades should always be recalculated
        otherwise return False when no problem has been seen in cache
    """

    def setUp(self):

        def fake_find_key(key):
            self.assertIsInstance(key, LmsKeyValueStore.Key)
            if key.block_scope_id:
                fake_found = MagicMock()
                fake_found.grade = key.student_id
                return fake_found
            else:
                return None

        self.fake_model_data_cache = MagicMock()
        self.fake_model_data_cache.find = fake_find_key

    def fake_module(self, is_in_cache, recalculate):
        output = MagicMock()
        output.location = is_in_cache
        output.always_recalculate_grades = recalculate
        return output

    def test_not_in_cache(self):
        #Test returning false when not always-recalculating-grades and when no problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(False, False) for i in range(5)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertFalse(result)

    def test_first_in_cache(self):
        #Test returning true when the first problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False)] + [self.fake_module(False, False) for i in range(7)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_last_in_cache(self):
        #Test returning true when the last problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(False, False) for i in range(3)] + [self.fake_module(True, False)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_all_in_cache(self):
        #Test returning true when all problems have been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False) for i in range(9)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_always_recalculate(self):
        #Test returning true when a module's grades should always be recalculated, even if False otherwise
        fake_xmoduledescriptors = [self.fake_module(False, True) for i in range(2)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_empty_list(self):
        #Test returning false when the list of xmodule descriptors is empty
        result = grades.find_should_grade_section([], self.fake_model_data_cache, 42)
        self.assertFalse(result)


class TestFindAttempted(unittest.TestCase):

    """
    Test the find_attempted method.
    """

    def setUp(self):

        def fake_find_key(key):
            self.assertIsInstance(key, LmsKeyValueStore.Key)
            if key.block_scope_id:
                fake_found = MagicMock()
                fake_found.grade = key.student_id
                return fake_found
            else:
                return None

        self.fake_model_data_cache = MagicMock()
        self.fake_model_data_cache.find = fake_find_key

    def fake_module(self, is_in_cache):
        output = MagicMock()
        output.location = is_in_cache
        return output

    def test_not_attempted(self):
        #Test returning false when student has not attempted problem
        fake_module = self.fake_module(False)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, None)
        self.assertFalse(result)

    def test_no_grade(self):
        #Test returning false when student has attempted problem, but grade is None
        fake_module = self.fake_module(True)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, None)
        self.assertFalse(result)

    def test_has_grade(self):
        #Test returning true when student has attempted problem and has a grade
        fake_module = self.fake_module(True)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, 3.0)
        self.assertTrue(result)


class TestGetScore(unittest.TestCase):

    """
    Tests the get_score method.

    get_score should:
        return (None, None):
            if the problem doesn't have a score
            if the problem couldn't be loaded
            if the user is not authenticated
        return (correct, total) otherwise
        reweight the problem correctly if specified
        not reweight a problem with zero total points
    """

    def setUp(self):

        def fake_find_key(key):
            self.assertIsInstance(key, LmsKeyValueStore.Key)
            if key.block_scope_id:
                fake_found = MagicMock()
                fake_found.grade = key.student_id[0]
                fake_found.max_grade = key.student_id[1]
                return fake_found
            else:
                return None

        self.fake_model_data_cache = MagicMock()
        self.fake_model_data_cache.find = fake_find_key

        def module_creator(descriptor):
            #Returns a problem mock
            output = MagicMock()
            output.get_score = lambda: {'score': 8.0, 'total': 9.0}
            output.max_score = lambda: 9.0
            return output

        self.module_creator = module_creator

        self.course_id = None

        self.user = MagicMock()
        self.user.id = (5.0, 7.0)  # fed into fake_find_key(key)'s output
        self.user.is_authenticated = lambda: True

        self.problem_descriptor = MagicMock()
        self.problem_descriptor.always_recalculate_grades = False
        self.problem_descriptor.has_score = True
        # if .location is not None, problem descriptor is "found" by fake_find_key
        self.problem_descriptor.location = "problem location"
        self.problem_descriptor.weight = None

        self.call_result = lambda: grades.get_score(
            self.course_id, self.user, self.problem_descriptor, self.module_creator, self.fake_model_data_cache
        )

    def test_simple(self):

        model_data_cache = self.fake_model_data_cache

        self.assertEquals(self.call_result(), (5.0, 7.0))

    def test_not_in_cache(self):

        self.problem_descriptor.location = None

        #0/9 instead of 8/9 because if the problem is not in the cache, we assume it is ungraded.
        self.assertEquals(self.call_result(), (0.0, 9.0))

    def test_always_recalculate(self):

        self.problem_descriptor.always_recalculate_grades = True

        self.assertEquals(self.call_result(), (8.0, 9.0))

    def test_reweight(self):

        self.problem_descriptor.weight = 14.0

        self.assertEquals(self.call_result(), (10.0, 14.0))

    def test_failed_reweight(self):

        self.user.id = (0.0, 0.0)
        self.problem_descriptor.weight = 14.0

        self.assertEquals(self.call_result(), (0.0, 0.0))

    def test_unauthenticated(self):

        self.user.is_authenticated = lambda: False

        self.assertEquals(self.call_result(), (None, None))

    def test_not_has_score(self):

        self.problem_descriptor.has_score = False

        self.assertEquals(self.call_result(), (None, None))

    def test_student_module_grade_is_none(self):

        def fake_find_key(key):
            return None
        self.fake_model_data_cache.find = fake_find_key

        self.assertEquals(self.call_result(), (0.0, 9.0))

    def test_always_recalculate_get_score_is_none(self):

        def module_creator(descriptor):
            #Returns a problem mock
            output = MagicMock()
            output.get_score = lambda: None
            output.max_score = lambda: 9.0
            return output
        self.module_creator = module_creator
        self.problem_descriptor.always_recalculate_grades = True

        self.assertEquals(self.call_result(), (None, None))

    def test_not_in_cache_and_module_creator_returns_none(self):

        def module_creator(descriptor):
            return None
        self.module_creator = module_creator
        self.problem_descriptor.location = None

        self.assertEquals(self.call_result(), (None, None))

    def test_not_in_cache_and_total_is_none(self):

        def module_creator(descriptor):
            #Returns a problem mock
            output = MagicMock()
            output.get_score = lambda: {'score': 8.0, 'total': None}
            output.max_score = lambda: None
            return output
        self.module_creator = module_creator
        self.problem_descriptor.location = None

        self.assertEquals(self.call_result(), (None, None))
