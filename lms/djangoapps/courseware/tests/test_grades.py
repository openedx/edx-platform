"""
This is the start of a test for grades.
It is incomplete - we do not test answer_distributions or
progress_summary.
"""
from mock import MagicMock
import unittest

from xmodule.capa_module import CapaModule
from xmodule.seq_module import SequenceModule
from xmodule.graders import Score
from xmodule.modulestore.django import modulestore, editable_modulestore
from xmodule.modulestore.tests.factories import CourseFactory, XModuleItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from django.test.utils import override_settings
from django.test.client import RequestFactory

import courseware.grades as grades
import courseware.module_render as module_render
from courseware.model_data import LmsKeyValueStore, ModelDataCache
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE, TEST_DATA_XML_MODULESTORE
from student.tests.factories import UserFactory


class ProblemFactory(XModuleItemFactory):
    """
    A factory for problems.  Fills in the data needed for problems
    with sane defaults.
    """
    FACTORY_FOR = CapaModule
    
    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Does some pre-processing, before calling the XModuleItemFactory
        _create.
        kwargs:
        - problem_name - Mandatory, the url_name of the problem
        - parent_location - Mandatory, the parent of this xmodule
        - answer - The answer
        """
        name = kwargs.pop('problem_name')
        answer = kwargs.pop('answer', 42)
        text = '''
        <problem display_name="{name}" url_name="{name}">
          <numericalresponse answer="{answer}">
            <responseparam type="tolerance" default="0.00001"/> 
            <textline size="20" inline="true" trailing_text="kN"/>
          </numericalresponse>
        </problem>
        '''.format(name=name, answer=answer)
        kwargs.update({'data': text,})
        descriptor = XModuleItemFactory.create(**kwargs)
        # Now, change the graded flag, and do a bunch of voodoo to save this change.
        descriptor.lms.graded = True
        descriptor.weight = kwargs.pop('weight', 1)
        descriptor.save()
        editable_modulestore().update_metadata(descriptor.location, descriptor._model_data._kvs._metadata)
        return descriptor


class ProblemSetFactory(XModuleItemFactory):
    """
    A factory for problemsets.  They are marked as `graded`.
    Mandatory kwarg 'format' determines descriptor.lms.format.
    """
    FACTORY_FOR = SequenceModule

    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Sets some properties of descriptor.lms.
        """
        format = kwargs.pop('format')
        kwargs['category'] = 'problemset'
        descriptor = XModuleItemFactory.create(**kwargs)
        descriptor.lms.graded = True
        descriptor.lms.format = format
        descriptor.save()
        editable_modulestore().update_metadata(descriptor.location, descriptor._model_data._kvs._metadata)
        return descriptor


class RequestFactoryForModules(RequestFactory):
    """
    Makes fake requests good for instantiating modules.
    """
    def __new__(self):
        out = RequestFactory()
        out.META = MagicMock()
        out.is_secure = lambda: False
        out.get_host = lambda: 'fake_host'
        return out


def _flat(thing):
    """
    If thing is a list, return thing[0]
    else, return thing
    """
    if type(thing) == list:
        return thing[0]
    else:
        return thing


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class FactoryScoringTest(ModuleStoreTestCase):
    """
    Tests grading on a sample mongo course.
    """
    def setUp(self):
        # Set up Mako correctly.
        from mitxmako.middleware import MakoMiddleware
        MakoMiddleware()
        
        # Make the fake course
        self.toy_course = CourseFactory.create(grading_policy={
            "GRADER": [
                    {
                        "type": "Problem Set",
                        "min_count": 4,
                        "drop_count": 0,
                        "short_label": "PSET",
                        "weight": 0.4
                    },
                    {
                        "type": "Final",
                        "short_label": "Final",
                        "min_count": 1,
                        "drop_count": 0,
                        "weight": 0.6
                    }
                ],
                "GRADE_CUTOFFS": {
                    "Pass": 0.5
                }
            }
        )
        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactoryForModules()

        self.model_data_cache = ModelDataCache(
            [self.toy_course],
            self.toy_course.id,
            self.mock_user,
        )

        # Make some psets and an exam.  Course structure is as follows:
        # Pset 1
        #    1_1 - 2pts - Correct
        #    1_2 - 3pts - Correct
        #    1_3 - 4pts - Unanswered
        #    1_4 - 5pts - Correct
        # Pset 2
        #    2_1 - 10pts - Correct
        #    2_2 - 10pts - Incorrect
        # Final
        #    e_1 - 20pts - Unanswered
        #    e_2 - 10pts - Correct
        self.chapter1 = XModuleItemFactory(
            parent_location=self.toy_course.location,
            category='chapter',
        )
        self.ps1 = ProblemSetFactory(
            parent_location=self.chapter1.location,
            format='Problem Set'
        )
        self.problem1_1 = ProblemFactory(
            parent_location=self.ps1.location,
            problem_name='ps1_1',
            weight=2
        )
        self._answer_correctly(self.problem1_1)
        self.problem1_2 = ProblemFactory(
            parent_location=self.ps1.location,
            problem_name='ps1_2',
            weight=3
        )
        self._answer_correctly(self.problem1_2)
        self.problem1_3 = ProblemFactory(
            parent_location=self.ps1.location,
            problem_name='ps1_3',
            weight=4
        )
        self.problem1_4 = ProblemFactory(
            parent_location=self.ps1.location,
            problem_name='ps1_4',
            weight=5
        )
        self._answer_correctly(self.problem1_4)

        self.chapter2 = XModuleItemFactory(
            parent_location=self.toy_course.location,
            category='chapter',
        )
        self.ps2 = ProblemSetFactory(
            parent_location=self.chapter2.location,
            format='Problem Set',
        )
        self.problem2_1 = ProblemFactory(
            parent_location=self.ps2.location,
            problem_name='ps2_1',
            weight=10
        )
        self._answer_correctly(self.problem2_1)
        self.problem2_2 = ProblemFactory(
            parent_location=self.ps2.location,
            problem_name='ps2_2',
            weight=10
        )
        self._answer_incorrectly(self.problem2_2)

        self.chapter3 = XModuleItemFactory(
            parent_location=self.toy_course.location,
            category='chapter',
        )
        self.final_exam = ProblemSetFactory(
            parent_location=self.chapter3.location,
            format='Final',
        )
        self.probleme_1 = ProblemFactory(
            parent_location=self.final_exam.location,
            problem_name='e_1',
            weight=20
        )
        self.probleme_2 = ProblemFactory(
            parent_location=self.final_exam.location,
            problem_name='e_2',
            weight=10
        )
        self._answer_correctly(self.probleme_2)


    def _fetch_problem(self, descriptor):
        """
        Given a descriptor, return an xmodule.
        """
        return module_render.get_module_for_descriptor_internal(
            self.mock_user,
            descriptor,
            self.model_data_cache,
            self.toy_course.id,
            lambda *args: None,
            'blah',
        )

    def _answer_correctly(self, problem_descriptor):
        """
        Answer all parts of the given problem correctly.
        """
        problem_module = self._fetch_problem(problem_descriptor)
        answers = problem_module.lcp.get_question_answers()
        answers = {'input_' + key: _flat(value) for key, value in answers.iteritems()}
        problem_module.check_problem(answers)

    def _answer_incorrectly(self, problem_descriptor):
        """
        Answer all parts of this problem incorrectly.
        """
        problem_module = self._fetch_problem(problem_descriptor)
        answers = problem_module.lcp.get_question_answers()
        answers = {'input_' + key: 'wrong' for key in answers}
        problem_module.check_problem(answers)

    def test_course_grading(self):
        """
        Run the toy course through the grader, and check what comes out.
        """
        # First, reload the toy course descriptor.
        store = editable_modulestore('direct')
        self.toy_course = store.get_item(self.toy_course.location)
        grader_out = grades.grade(self.mock_user, self.request_factory, self.toy_course)
        print grader_out
        # Overall score
        self.assertAlmostEqual(grader_out['percent'], 0.32)
        breakdown = grader_out['section_breakdown']
        # Pset 1
        self.assertAlmostEqual(breakdown[0]['percent'], 0.7142857142857143)
        # Pset 2
        self.assertAlmostEqual(breakdown[1]['percent'], 0.5)
        # Pset 3 (unreleased)
        self.assertAlmostEqual(breakdown[2]['percent'], 0.0)
        # Overall problem sets
        self.assertAlmostEqual(grader_out['grade_breakdown'][0]['percent'], 0.12142857142857144)
        # Final
        self.assertAlmostEqual(grader_out['grade_breakdown'][1]['percent'], 0.2)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class ScoringTestCase(ModuleStoreTestCase):
    """
    Tests grading on a small sample xml course, found in
    common/test/data/score_test.

    This test is designed to detect whether changes to xmodule,
    modulestore, etc. break grading.  It is not designed to test whether
    every facet of grading works as advertised - the other tests below
    do that.
    """
    def setUp(self):
        self.location = ['i4x', 'edX', 'score_test', 'chapter', 'Overview']
        self.course_id = 'edX/score_test/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_id)

        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactoryForModules()

        self.model_data_cache = ModelDataCache(
            [self.toy_course],
            self.course_id,
            self.mock_user,
        )

        # Set up Mako correctly.
        from mitxmako.middleware import MakoMiddleware
        MakoMiddleware()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Answer some problems.  Course structure is as follows:
        # Pset 1 (ps01.xml)
        #    1_1 - 2pts - Correct
        #    1_2 - 3pts - Correct
        #    1_3 - 4pts - Unanswered
        #    1_4 - 5pts - Correct
        # Pset 2 (ps02.xml)
        #    2_1 - 10pts - Correct
        #    2_2 - 10pts - Incorrect
        # Final (exam.xml)
        #    e_1 - 20pts - Unanswered
        #    e_2 - 10pts - Correct
        p1_1 = self._fetch_problem('1_1')
        self._answer_correctly(p1_1)

        p1_2 = self._fetch_problem('1_2')
        self._answer_correctly(p1_2)

        p1_4 = self._fetch_problem('1_4')
        self._answer_correctly(p1_4)

        p2_1 = self._fetch_problem('2_1')
        self._answer_correctly(p2_1)

        p2_2 = self._fetch_problem('2_2')
        self._answer_incorrectly(p2_2)

        pe_2 = self._fetch_problem('e_2')
        self._answer_correctly(pe_2)

    def _fetch_problem(self, problem_name):
        """
        Return a problem module, given a problem url-name.
        """
        loc = ['i4x', 'edX', 'score_test', 'problem', problem_name]
        prob_descriptor = modulestore().get_instance(self.course_id, loc)
        prob = module_render.get_module_for_descriptor_internal(
            self.mock_user,
            prob_descriptor,
            self.model_data_cache,
            self.course_id,
            lambda *args: None,
            'blah',
        )
        return prob

    def _answer_correctly(self, problem_module):
        """
        Answer all parts of the given problem correctly.
        Modifies problem_module in-place.
        """
        answers = problem_module.lcp.get_question_answers()
        answers = {'input_' + key: _flat(value) for key, value in answers.iteritems()}
        problem_module.check_problem(answers)

    def _answer_incorrectly(self, problem_module):
        """
        Answer all parts of this problem incorrectly.
        """
        answers = problem_module.lcp.get_question_answers()
        answers = {'input_' + key: 'wrong' for key in answers}
        problem_module.check_problem(answers)

    def test_course_grading(self):
        """
        Run the toy course through the grader, and check what comes out.
        """
        grader_out = grades.grade(self.mock_user, self.request_factory, self.toy_course)
        # Overall score
        self.assertAlmostEqual(grader_out['percent'], 0.32)
        breakdown = grader_out['section_breakdown']
        # Pset 1
        self.assertAlmostEqual(breakdown[0]['percent'], 0.7142857142857143)
        # Pset 2
        self.assertAlmostEqual(breakdown[1]['percent'], 0.5)
        # Pset 3 (unreleased)
        self.assertAlmostEqual(breakdown[2]['percent'], 0.0)
        # Overall problem sets
        self.assertAlmostEqual(grader_out['grade_breakdown'][0]['percent'], 0.12142857142857144)
        # Final
        self.assertAlmostEqual(grader_out['grade_breakdown'][1]['percent'], 0.2)


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
        compute_graded_total(section, student, course_id, model_data_cache, request)
        - section['section_descriptor'] returns the descriptor for this section.
        - student needs an id
        - All other paramenters are touched through helper functions only.

        Functions to mock:
        grades.should_grade_section(descriptor, model_data_cache, student_id) -> True/False
        .module_render.get_module_for_descriptor(student, request, descriptor, model_data_cache, course_id) -> Xmodule
        grades.yield_dynamic_descriptor_descendents(descriptor, create_module) -> iter through descriptors
        grades.get_score(course_id, student, descriptor, create_module, model_data_cache) -> (correct, total)
        grades.find_attempted(descriptor, model_data_cache, student_id) -> True/False
        """

        section = {'section_descriptor': MagicMock(), 'xmoduledescriptors': MagicMock()}
        student = MagicMock()
        student.id = 'my id'
        course_id = 'course id'
        model_data_cache = MagicMock()  # We will never query the mdc directly.
        request = MagicMock()   # Same as above.

        # Monkey patching!
        def fake_should_grade_section(descriptors, model_data_cache, student_id):
            """ Always grade :) """
            return True
        grades.should_grade_section = fake_should_grade_section

        def fake_get_module_for_descriptor(student, request, descriptor, model_data_cache, course_id):
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

        def fake_get_score(course_id, student, descriptor, create_module, model_data_cache):
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

        def fake_find_attempted(descriptor, model_data_cache, student_id):
            """Always return True. """
            return True
        grades.find_attempted = fake_find_attempted

        # Actually do the test.
        graded_total, raw_scores = grades.compute_graded_total(
            section['section_descriptor'], section['xmoduledescriptors'],
            student, course_id, model_data_cache, request
        )
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
        compute_graded_total(section, student, course_id, model_data_cache, request)
        grade_for_percentage(cutoffs, percent_summary)
        """
        student = MagicMock()
        request = MagicMock()
        course = MagicMock()
        course.grading_context = {
            'graded_sections': {
                'HW': [{'section_descriptor': 'HW1'}, {'section_descriptor': 'HW2'}],
                'Quiz': [{'section_descriptor': 'Quiz1'}],
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
        model_data_cache = MagicMock()

        def fake_compute_graded_total(section_descriptor, xmd, student, course_id, model_data_cache, request):
            """
            A fake compute_graded_total.  Expects a string for section_descriptor,
            instead of a real section descriptor.
            """
            if section_descriptor == 'HW1':
                return (
                    Score(4.0, 10.0, True, 'HW1', ),  # attempted=True
                    ['RS1']
                )
            elif section_descriptor == 'HW2':
                return (
                    Score(0.0, 10.0, True, 'HW2', ),  # attempted=False
                    ['RS2']
                )
            elif section_descriptor == 'Quiz1':
                return (
                    Score(85.0, 100.0, True, 'Quiz1', ),  # attempted=True
                    ['RS3']
                )
        grades.compute_graded_total = fake_compute_graded_total

        def fake_grade_for_percentage(cutoffs, percent_summary):
            """A mock of grade_for_percentage"""
            return 'A'
        grades.grade_for_percentage = fake_grade_for_percentage

        grade_summary = grades.grade(student, request, course, model_data_cache=model_data_cache, keep_raw_scores=True)
        reload(grades)

        print grade_summary['totaled_scores']
        self.assertTrue(grade_summary['percent'] == 64.5)
        self.assertTrue('HW' in grade_summary['totaled_scores'])
        self.assertTrue('HW' in grade_summary['totaled_scores'])
        self.assertTrue('Quiz' in grade_summary['totaled_scores'])
        self.assertTrue(grade_summary['raw_scores'] == ['RS1', 'RS2', 'RS3'])
        self.assertTrue(grade_summary['grade'] == 'A')



class TestShouldGradeSection(unittest.TestCase):
    """
    Test should_grade_section.

    should_grade_section should:
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
        result = grades.should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertFalse(result)

    def test_first_in_cache(self):
        #Test returning true when the first problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False)] + [self.fake_module(False, False) for i in range(7)]
        result = grades.should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_last_in_cache(self):
        #Test returning true when the last problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(False, False) for i in range(3)] + [self.fake_module(True, False)]
        result = grades.should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_all_in_cache(self):
        #Test returning true when all problems have been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False) for i in range(9)]
        result = grades.should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_always_recalculate(self):
        #Test returning true when a module's grades should always be recalculated, even if False otherwise
        fake_xmoduledescriptors = [self.fake_module(False, True) for i in range(2)]
        result = grades.should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_empty_list(self):
        #Test returning false when the list of xmodule descriptors is empty
        result = grades.should_grade_section([], self.fake_model_data_cache, 42)
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
