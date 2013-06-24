"""
Unit tests on the models that make up automated content testing
"""

from django.test import TestCase
from textwrap import dedent
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore
from content_testing.models import ContentTest, hash_xml, hash_xml_structure, condense_attributes, remove_xml_wrapper, condense_dict
from capa.tests.response_xml_factory import CustomResponseXMLFactory
from lxml import etree
from mock import patch


# disable sillly pylint violations
# pylint: disable=W0212
# pylint: disable=W0201
class ContentTestTestCase(ModuleStoreTestCase):
    """
    set up a content test to test
    """

    SCRIPT = dedent("""
    def is_prime (n):
        primality = True
        for i in range(2,int(math.sqrt(n))+1):
            if n%i == 0:
                primality = False
                break
        return primality

    def test_prime(expect,ans):
        a1=int(ans[0])
        a2=int(ans[1])
        return is_prime(a1) and is_prime(a2)""").strip()
    NUM_INPUTS = 2  # tied to script

    HTML_SUMMARY = dedent("""
    <table>
        <tr>
            <td>
                Inputs:
            </td>
            <td>
                Should Be:
            </td>
            <td>
                Verdict:
            </td>
        </tr>
        <tr>
            <td>
                <ol>
                    <li> 5 </li>
                    <li> 174440041 </li>
                </ol>
            </td>
            <td>
                correct
            </td>
            <td>
                 - Not Yet Run - 
            </td>
        <tr>
    </table>""").strip()

    VERDICT_PASS = "Pass"
    VERDICT_FAIL = "Fail"
    VERDICT_ERROR = ContentTest.ERROR
    VERDICT_NONE = ContentTest.NONE

    def setUp(self):
        """
        create all the tools to test content_tests
        """

        #course in which to put the problem
        self.course = CourseFactory.create()
        assert self.course

        # make the problem
        problem_xml = CustomResponseXMLFactory().build_xml(
            script=self.SCRIPT,
            cfn='test_prime',
            num_inputs=self.NUM_INPUTS)

        self.problem = ItemFactory.create(
            parent_location=self.course.location,
            data=problem_xml,
            category='problem')

        # sigh
        self.input_id_base = self.problem.id.replace('://', '-').replace('/', '-')

        # saved responses for making tests
        self.response_dict_correct = {
            self.input_id_base + '_2_1': '5',
            self.input_id_base + '_2_2': '174440041'
        }
        self.response_dict_incorrect = {
            self.input_id_base + '_2_1': '4',
            self.input_id_base + '_2_2': '541098'
        }

        self.response_dict_error = {
            self.input_id_base + '_2_1': 'anyone lived',
            self.input_id_base + '_2_2': 'in a pretty how town'
        }
        assert self.problem

        # Make a collection of ContentTests to test
        self.pass_correct = ContentTest(
            location=self.problem.location,
            should_be='correct',
            response_dict=self.response_dict_correct
        )

        self.pass_incorrect = ContentTest(
            location=self.problem.location,
            should_be='incorrect',
            response_dict=self.response_dict_incorrect
        )

        self.fail_correct = ContentTest(
            location=self.problem.location,
            should_be='incorrect',
            response_dict=self.response_dict_correct
        )

        self.fail_incorrect = ContentTest(
            location=self.problem.location,
            should_be='correct',
            response_dict=self.response_dict_incorrect
        )

        self.fail_error = ContentTest(
            location=self.problem.location,
            should_be='correct',
            response_dict=self.response_dict_error
        )

        self.pass_error = ContentTest(
            location=self.problem.location,
            should_be="error",
            response_dict=self.response_dict_error)


class WhiteBoxTestCase(ContentTestTestCase):
    """
    test that inner methods are working
    """

    def test_make_capa(self):
        '''test that the capa instantiation happens properly'''
        test_model = ContentTest(
            location=self.problem.location,
            should_be='Correct')

        capa = test_model.capa_problem()

        #assert no error
        assert self.SCRIPT in capa.problem_text

    def test_create_children(self):
        '''test that the ContentTest is created with the right structure'''

        test_model = ContentTest(
            location=str(self.problem.location),
            should_be='Correct')

        #check that the response created properly
        responses = test_model.responses
        self.assertEqual(len(responses), 1)

        #and the input
        self.assertEqual(len(responses[0].inputs), self.NUM_INPUTS)

    def test_create_dictionary(self):
        """
        tests the constructions of the response dictionary
        """

        test_model = ContentTest(
            location=self.problem.location,
            should_be='Correct',
            response_dict=self.response_dict_correct
        )

        created_dict = test_model.response_dict

        self.assertEqual(self.response_dict_correct, created_dict)

    def test_remake_dict(self):
        """
        tests the internal functionality of remaking the dictionary through the children
        """
        test_model = self.pass_correct

        # delete the dict attribute
        del test_model.response_dict

        #remake the attribute
        test_model._remake_dict_from_children()

        # make sure they match
        self.assertEqual(self.response_dict_correct, test_model.response_dict)


class MakeVerdictTestCase(ContentTestTestCase):
    """
    a few tests for the _make_verdict method
    """

    def setUp(self):
        super(MakeVerdictTestCase, self).setUp()
        response_dict_with_blank = {
            self.input_id_base + '_2_1': '',
            self.input_id_base + '_2_2': '174440041'
        }

        self.pass_correct_with_blank = ContentTest(
            location=self.problem.location,
            should_be='Correct',
            response_dict=response_dict_with_blank
        )

        self.mockup_correctmap_mixed = {
            self.input_id_base + '_2_1': {'correctness': 'incorrect'},
            self.input_id_base + '_2_2': {'correctness': 'correct'}
        }

    def test_pass_with_blank(self):
        """
        tests that blank entries are ignored
        """

        verdict = self.pass_correct_with_blank._make_verdict(self.mockup_correctmap_mixed)
        self.assertEqual(verdict, self.VERDICT_PASS)

    def test_mixed_fails_correct(self):
        """
        test that a mixed dictionary is not correct
        """

        test_model = self.pass_correct
        verdict = test_model._make_verdict(self.mockup_correctmap_mixed)
        self.assertEqual(verdict, self.VERDICT_FAIL)

    def test_mixed_fails_incorrect(self):
        """
        test that a mixed dictionary is not incorrect
        """

        test_model = self.pass_incorrect
        verdict = test_model._make_verdict(self.mockup_correctmap_mixed)
        self.assertEqual(verdict, self.VERDICT_FAIL)

    def test_mixed_fails_error(self):
        """
        test that a mixed dictionary is not error
        """

        test_model = self.pass_error
        verdict = test_model._make_verdict(self.mockup_correctmap_mixed)
        self.assertEqual(verdict, self.VERDICT_FAIL)


class BlackBoxTestCase(ContentTestTestCase):
    """
    test overall behavior of the ContentTest model
    """

    def test_pass_correct(self):
        '''test that it passes with correct answers when it should'''

        # run the test
        self.pass_correct.run()

        # make sure it passed
        self.assertEqual(self.VERDICT_PASS, self.pass_correct.verdict)

    def test_fail_incorrect(self):
        '''test that it fails with incorrect answers'''

        # run the testcase
        self.fail_incorrect.run()

        # make sure it failed
        self.assertEqual(self.VERDICT_FAIL, self.fail_incorrect.verdict)
        assert 'incorrect' in self.fail_incorrect.message

    def test_pass_incorrect(self):
        '''test that it passes with incorrect'''

        # run the test
        self.pass_incorrect.run()

        # make sure it passed
        self.assertEqual(self.VERDICT_PASS, self.pass_incorrect.verdict)

    def test_fail_correct(self):
        '''test that it fails with correct answers'''

        # run the testcase
        self.fail_correct.run()

        # make sure it failed
        self.assertEqual(self.VERDICT_FAIL, self.fail_correct.verdict)
        assert 'correct' in self.fail_correct.message

    def test_pass_error(self):
        """
        test that we get a pass when it expects and gets an error
        """
        # run the testcae
        self.pass_error.run()

        # make sure it passed
        self.assertEqual(self.VERDICT_PASS, self.pass_error.verdict)

    def test_fail_error(self):
        """
        Test that a badly formatted dictionary results in error
        """

        test_model = self.fail_error
        test_model.run()

        self.assertEqual(self.VERDICT_ERROR, test_model.verdict)

    def test_reset_verdict(self):
        '''test that changing things resets the verdict'''

        test_model = self.pass_correct

        # run the testcase (generates verdict)
        test_model.run()

        # update test
        test_model.response_dict = self.response_dict_incorrect
        test_model.todict()

        #ensure that verdict is now null
        self.assertEqual(self.VERDICT_NONE, test_model.verdict)

    def test_change_dict(self):
        '''test that the verdict changes with the new dictionary on new run'''

        test_model = self.pass_correct

        # update test
        test_model.response_dict = self.response_dict_incorrect
        test_model.todict()

        # run the test
        test_model.run()

        # assert that the verdict is now self.VERDICT_FAIL
        self.assertEqual(self.VERDICT_FAIL, test_model.verdict)

    def test_todict_idempotent(self):
        """
        tests that we get the same object after instantiating from dict
        """
        self.maxDiff = None
        test_dict = self.pass_correct.todict()
        new_test = ContentTest(**test_dict)

        self.assertEqual(new_test.todict(), self.pass_correct.todict())

    @patch('content_testing.models.ContentTest.capa_problem')
    @patch('content_testing.models.ContentTest.rematch_if_necessary')
    def test_instantiate_from_todict(self, capa_problem, rematch_if_necessary):
        """
        test that other than the structure matching (which always will
        require fetching the capa somehow), no capa is used for instantiation
        from saved dict. This test should fail if .capa_problem() is ever
        called, not result in error.
        """
        test_dict = self.pass_correct.todict()
        new_test = ContentTest(**test_dict)

        assert not (new_test.capa_problem.called)


    def test_partial_dict(self):
        """
        test that a model instantiated with a incomplete dict will
        fill in the remaining values with blanks
        """

        self.response_dict_correct.popitem()
        incomplete_dict = self.response_dict_correct
        incomplete_test = ContentTest(
            location=self.problem.location,
            response_dict=incomplete_dict
        )

        assert '' in incomplete_test.response_dict.values()


class RematchingTestCase(ContentTestTestCase):
    """
    tests the ability to rematch itself to an edited problem
    """

    def setUp(self):
        """
        create new sructure to test smart restructuring capabilities
        """

        super(RematchingTestCase, self).setUp()

        self.new_xml = CustomResponseXMLFactory().build_xml(
            script=self.SCRIPT,
            cfn='test_prime',
            num_inputs=self.NUM_INPUTS + 1)

        self.new_problem = ItemFactory.create(
            parent_location=self.course.location,
            data=self.new_xml,
            category='problem')

        self.test_model = self.pass_correct

    def update_problem_xml(self, new_xml_string):
        """
        update the problem xml and do the other acrobatics to update everything
        consistantly
        """

        # update the problem
        modulestore().update_item(self.problem.location, new_xml_string)

        # this gets rid of the _draft nonsense, which makes hard-coded dicts easier.
        modulestore().publish(self.problem.location, 0)

        # force ContentTest to refetch module
        # If we just set .module=None, then we force the ContentTest object
        # to refetch, and thus effectively test the rematching capabilities.
        # Hoerver, this only tests for when the COntentTest isn't being reloaded
        # from the database, which would be most of the time.  Thus, we test with
        # both.
        self.test_model2 = ContentTest(**self.test_model.todict())
        self.test_model.module = None

    def test_matches(self):
        """
        test that the model knows when it still matches the problem
        """

        assert self.pass_correct._still_matches()

    def test_not_matches_new_xml(self):
        """
        test that when the xml of the capa problem gets updated
        the model knows
        """

        # change the problem by adding another textline
        self.update_problem_xml(self.new_xml)

        assert not(self.test_model._still_matches())

    def test_new_dict_blank(self):
        """
        test rebuilding the dictionary with a different response
        """

        # the dictioanry, after fixing, should have blank answers
        new_dict = {
            self.input_id_base + '_2_1': '',
            self.input_id_base + '_2_2': '',
            self.input_id_base + '_2_3': ''
        }

        # change the problem by adding another textline
        self.update_problem_xml(self.new_xml)

        self.test_model.rematch_if_necessary()
        # self.assertEqual(new_dict, self.test_model.response_dict)
        self.assertEqual(new_dict, self.test_model2.response_dict)

    def test_append(self):
        """
        test adding a new response at the end and then rebuilding
        """

        # add a response at the end
        new_response_xml = etree.XML("<customresponse cfn=\"test_prime\"><textline/><textline/><textline/></customresponse>")
        new_xml = self.pass_correct.capa_problem().tree
        new_xml.append(new_response_xml)
        new_xml_string = etree.tostring(new_xml)
        # the response dict should look like
        two_responses_dict = {
            self.input_id_base + '_3_1': '',
            self.input_id_base + '_3_2': '',
            self.input_id_base + '_3_3': ''
        }
        two_responses_dict.update(self.response_dict_correct)

        # change the problem by adding another response at end
        self.update_problem_xml(new_xml_string)
        self.test_model.rematch_if_necessary()
        self.assertEqual(two_responses_dict, self.test_model.response_dict)
        self.assertEqual(two_responses_dict, self.test_model2.response_dict)

    def test_insert(self):
        """
        adding response at beginning of problem
        """

        new_xml_string = dedent("""
            <problem>

            <script type="loncapa/python">

            def is_prime (n):
              primality = True
              for i in range(2,int(math.sqrt(n))+1):
                if n%i == 0:
                    primality = False
                    break
              return primality

            def test_prime(expect,ans):
              a=int(ans)
              return is_prime(a)

            </script>

            <p>Enter a prime number</p>
            <customresponse cfn="test_prime">
              <textline/>
              <textline/>
              <textline/>
            </customresponse>
            <customresponse cfn="test_prime">
              <textline/>
              <textline/>
            </customresponse>
            </problem>""")

        # the response dict should look like
        two_responses_dict = {
            self.input_id_base + '_3_1': '5',
            self.input_id_base + '_3_2': '174440041',
            self.input_id_base + '_2_1': '',
            self.input_id_base + '_2_2': '',
            self.input_id_base + '_2_3': ''
        }

        # change the problem by adding another response at end
        self.update_problem_xml(new_xml_string)

        self.test_model.rematch_if_necessary()
        self.assertEqual(two_responses_dict, self.test_model.response_dict)

    def test_change_attributes(self):
        """
        test that changing the attributes of the mxl doesn't cuase any net restructuring
        """

        # add attribute values
        test_model = self.pass_correct
        xml = test_model.capa_problem().tree
        for child in xml:
            child.attrib['samba'] = 'deamon'

        # save these to the capa_problem
        self.update_problem_xml(etree.tostring(xml))

        # make sure that no restructuring happens
        self.test_model.rematch_if_necessary()
        self.assertEqual(self.response_dict_correct, self.test_model.response_dict)

    def test_delete_response(self):
        """
        test removing responses that no longer match any in the problem
        (changing problem location accomplishes this)
        """

        # change location on the test
        test_model = self.pass_correct
        test_model.location = self.new_problem.location
        # force it to refetch from mongo
        test_model.module = None

        # make it rematch itself
        test_model.rematch_if_necessary()

        # assert that the new dictionary has no values
        self.assertEqual(["", "", ""], test_model.response_dict.values())

    def test_fuzzy_rematching_insert(self):
        """
        test matching capabilities when things are slightly off
        """

        new_xml_string = dedent("""
            <problem>

            <script type="loncapa/python">

            def is_prime (n):
              primality = True
              for i in range(2,int(math.sqrt(n))+1):
                if n%i == 0:
                    primality = False
                    break
              return primality

            def test_prime(expect,ans):
              a=int(ans)
              return is_prime(a)

            </script>

            <p>Enter a prime number</p>
            <customresponse cfn="test_prime">
              <textline/>
              <textline/>
              <textline/>
            </customresponse>
            <customresponse cfn="test_prome">
              <textline/>
              <textline/>
            </customresponse>
            </problem>""")

        # the response dict should look like
        two_responses_dict = {
            self.input_id_base + '_3_1': '5',
            self.input_id_base + '_3_2': '174440041',
            self.input_id_base + '_2_1': '',
            self.input_id_base + '_2_2': '',
            self.input_id_base + '_2_3': ''
        }

        # change the problem by adding another response at end
        self.update_problem_xml(new_xml_string)
        self.test_model.rematch_if_necessary()
        self.assertEqual(two_responses_dict, self.test_model.response_dict)

    def test_change_ids(self):
        """
        While getting rid of the _draft nonsense made it easier to write
        the tests, we still need to make sure that that doesn't break things
        """

        # store the old dict
        old_dict = self.pass_correct.response_dict

        # update the problem with same xml that it already has
        # This should make all the id's contain _draft
        xml = self.problem.data
        modulestore().update_item(self.problem.location, xml)

        new_model = ContentTest(**self.pass_correct.todict())
        new_model.run()

        # assert that the values haven't changed
        self.assertItemsEqual(old_dict.values(), new_model.response_dict.values())

        # assert that the dicts themselves are different, since if they are the
        # same, than this test is not testing what it means to.
        self.assertNotEqual(old_dict, new_model.response_dict)

        # assert that it still passes
        self.assertEqual(self.VERDICT_PASS, new_model.verdict)


class HelperFunctionsTestCase(TestCase):
    """
    tests for the xml helper functions
    """

    def test_hash_xml_same(self):
        """
        test that the hash function ignors the right things
        """

        xml1 = etree.XML("<root root_id=\"3\"><child id=\"234\"/></root>")
        xml2 = etree.XML("<root><child/></root>")

        self.assertEqual(hash_xml(xml1), hash_xml(xml2))

    def test_hash_xml_different(self):
        """
        test that the hash function includes the right things
        """

        xml1 = etree.XML("<root root_id=\"3\" borgle=\"whee\"><child id=\"234\"/></root>")
        xml2 = etree.XML("<root><child/></root>")

        self.assertNotEqual(hash_xml(xml1), hash_xml(xml2))

    def test_hash_xml_structure_same(self):
        """
        Test that structure hash ignores all attributes
        """

        xml1 = etree.XML("<root root_id=\"3\" borgle=\"whee\"><child id=\"234\"/><child mop=\"234\"/></root>")
        xml2 = etree.XML("<root><child/><child/></root>")

        self.assertEqual(hash_xml_structure(xml1), hash_xml_structure(xml2))

    def test_hash_xml_structure_different(self):
        """
        Test that structure hash ignores all attributes
        """

        xml1 = etree.XML("<root root_id=\"3\" borgle=\"whee\"><child id=\"234\"/><child/><child mop=\"234\"/></root>")
        xml2 = etree.XML("<root><child/><child/></root>")

        self.assertNotEqual(hash_xml_structure(xml1), hash_xml_structure(xml2))

    def test_remove_wrapper_xml(self):
        """
        test the function used to strip out forms with lxml input
        """

        xml1 = etree.XML("<root><a><b/><c/><a><d/></a></a></root>")
        xml2 = etree.XML("<root><b/><c/><d/></root>")

        processed_xml = remove_xml_wrapper(xml1, 'a')

        self.assertEqual(etree.tostring(xml2), etree.tostring(processed_xml))

    def test_remove_wrapper_string(self):
        """
        test the function used to strip out forms with text input
        """

        xml1 = "<root><a><b/><c/><a><d/></a></a></root>"
        xml2 = "<root><b/><c/><d/></root>"

        processed_xml = remove_xml_wrapper(xml1, 'a')

        self.assertEqual(xml2, processed_xml)

    def test_condense_attributes(self):
        """
        tests a helper function for recursively generating a attribute dictionary
        """

        xml = etree.XML("""<customresponse cfn="test_csv" expect="0, 1, 2, 3, 3">
            <textline size="50" correct_answer="0, 1, 2, 3, 3"/>
          </customresponse>""")

        dictionary = {'cfn': 'test_csv', 'expect': '0, 1, 2, 3, 3', 'correct_answer': '0, 1, 2, 3, 3'}

        self.assertEqual(dictionary, condense_attributes(xml))

    def test_condense_dict(self):
        """
        test helper function for squashing a dictionary
        """

        to_squash = {'all in green ': 'went my love riding'}
        squashed = 'all in green went my love riding'

        self.assertEqual(condense_dict(to_squash), squashed)
