"""
Django models used to store and manipulate content tests
"""
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from contentstore.views.preview import load_preview_module
from lxml import etree
from copy import deepcopy
from difflib import SequenceMatcher
# pylint: disable=E1101


def hash_xml(tree):
    """
    create a hash of the etree xml element solely based on 'meaningful' parts of the xml string
    """
    tree = deepcopy(tree)
    remove_ids(tree, (lambda k: k[-2:] == 'id' or k == 'size'))
    return etree.tostring(tree).__hash__()


def remove_ids(tree, should_be_removed):
    """
    remove all keys for which `should_be_removed(attrib)` returns true
    """
    for attrib in tree.attrib:
        if should_be_removed(attrib):
            tree.attrib.pop(attrib)

    # do the same to all the children
    for child in tree:
        remove_ids(child, should_be_removed)


def hash_xml_structure(tree):
    """
    create hash of xml that ignores all attributes except ones involving `id`
    """
    tree = deepcopy(tree)
    remove_ids(tree, (lambda k: True))
    return etree.tostring(tree).__hash__()


def condense_attributes(tree):
    """
    take an XML tree and collect all `meaningful` attributes into single dict
    """

    tree = deepcopy(tree)
    remove_ids(tree, (lambda k: k[-2:] == 'id' or k == 'size'))
    attrib = tree.attrib

    # add in childrens attributes
    for child in tree:
        attrib.update(condense_attributes(child))

    return attrib


def remove_xml_wrapper(tree, name):
    """
    Remove all elements by the name of `name` in `tree` but keep
    any children by inserting them into the location of `name`.

    Return a new tree.

    Accepts either lxml.etree.Element objects or strings.
    """

    # we want to return the same type we were given
    tree = deepcopy(tree)
    return_string = False
    if isinstance(tree, basestring):
        tree = etree.XML(tree)
        return_string = True

    for item in tree.iterfind('.//'+name):
        # reverse children for inserting
        children = [elts for elts in item]
        children.reverse()

        # index for insertion
        index = item.getparent().index(item)

        # insert the form contents
        for child in children:
            item.getparent().insert(index, child)

        # remove item
        item.getparent().remove(item)

    # return a string if that is what we were given
    if return_string:
        tree = etree.tostring(tree)

    return tree


def condense_dict(dictionary):
    """
    returns a string ondensation of the dictionary for %% comparison purposes.

    {'tree': 3, 'apple': 'hello'} -> 'tree3applehello'
    """

    return ''.join([str(key)+str(dictionary[key]) for key in dictionary])


def closeness(model, responder):
    """
    Return a value between 0 and ~1 representing how good a match these two are.
    0 = Terribad.  1 = identical. 1.01 = identical in original location.
    """

    # no match if the structure is different
    if model.structure_hash != hash_xml_structure(responder.xml):
        return 0

    # almost all the xml will be the same since they have the same structure anyway.
    # Thus, we look at just the attributes that are meaningful
    model_xml = etree.XML(model.xml_string)
    resp_xml = responder.xml

    model_string = condense_dict(condense_attributes(model_xml))
    responder_string = condense_dict(condense_attributes(resp_xml))

    # use difflib to calculate string closeness
    seq = SequenceMatcher(None, model_string, responder_string)
    ratio = seq.ratio()

    # favor matches that are in the same location (this might need tweaking!!)
    if model.string_id == responder.id:
        ratio = 1.01 * (1 - (1 - ratio) ** (1.2))
    return ratio


class ContentTest(object):
    """
    Model for a user-created test for a capa-problem
    """

    ERROR = "error"
    PASS = "Pass"
    FAIL = "Fail"
    NONE = " - Not Yet Run - "

    SHOULD_BE = {
        "correct": "correct",
        "incorrect": "incorrect",
        "error": "error"
    }

    def __init__(
        self,
        location,
        should_be=SHOULD_BE['correct'],
        response_dict=None,
        verdict=NONE,
        message=NONE,
        override_state=None,
        responses=None,
        module=None,
        id=0
    ):
        """
        To instantiate a content_test, we use the following information:
        - location          -- locaiton of capa_problem() being tested
        - should_be         -- what the expected return of the grader is (Correct, Incorrect, etc.)
        - response_dict     -- dictionary to be turned into the grade
        - verdict           -- result of the test (pass, fail, not run, Error)
        - message           -- message about test (error message, etc)
        - override_state    -- dictionary of values to define the state of the lcp (seed, etc)
        - module            -- CapaModule
        - id                -- unique number within the descriptor
        """
        self.location = location
        self.should_be = should_be
        self.response_dict = response_dict or {}
        self.verdict = verdict
        self.message = message
        self.override_state = override_state or {}
        self.module = module
        self.id = id

        # list of children
        # the None case is handled in self._create_children()
        self.responses = responses

        # used to detect edits
        self._old_resp_dict = self.response_dict
        self._create_children()
        self.rematch_if_necessary()

    @classmethod
    def construct_preview_module(cls, location, descriptor=None):
        """
        construct a new preview capa module
        """
        # create a preview of the capa_module()
        if descriptor is None:
            descriptor = modulestore().get_item(Location(location))

        preview_module = load_preview_module(0, descriptor)

        return preview_module

    def capa_problem(self):
        """
        create the capa_problem().
        """

        # create a LoncapaProblem with the right state
        new_lcp_state = self.capa_module().get_state_for_lcp()  # pylint: disable=E1103
        new_lcp_state.update(self.override_state)
        lcp = self.capa_module().new_lcp(new_lcp_state)  # pylint: disable=E1103

        return lcp

    def capa_module(self):
        """
        resturns a preview instance of the capa module pointed to by
        self.location
        """
        # fetch from mongo if we don't already have a module
        if self.module is None:
            self.module = ContentTest.construct_preview_module(self.location)

        return self.module

    def todict(self, *arg, **kwargs):
        """
        Returns a dict describing this content test
        """

        # if we changing the dictionary, update the verdict to NONE
        if self._old_resp_dict != self.response_dict:
            self.verdict = self.NONE

        return {
            'location': self.location,
            'should_be': self.should_be,
            'response_dict': self.response_dict,
            'verdict': self.verdict,
            'message': self.message,
            'override_state': self.override_state,
            'responses': [resp_test.todict() for resp_test in self.responses],
            'id': self.id
        }

    def run(self):
        """
        run the test, and see if it passes
        """

        # process dictionary that is the response from grading
        grade_dict = self._evaluate(self.response_dict)

        # compare the result with what is should be
        self.verdict = self._make_verdict(grade_dict)

        # on error, the message gets set when that error is handled
        # (in self._evaluate())
        if self.verdict == self.FAIL:
            if self.should_be == self.SHOULD_BE["correct"]:
                self.message = "%s: Input got evaluated as %s" % (self.verdict, self.SHOULD_BE["incorrect"])
            else:
                self.message = "%s: Input got evaluated as %s" % (self.verdict, self.SHOULD_BE["correct"])
        elif self.verdict == self.PASS:
            self.message = self.verdict + " :)"

        # write the change to the database and return the result
        return self.verdict

    def rematch_if_necessary(self):
        """
        Rematches itself to its problem if it no longer matches.
        Reassigns hashes to response models if they no longer
        match but the structure still does (so future matching
        can happen).
        """

        if not self._still_matches():
            self._rematch()
        else:
            self._reassign_hashes_if_necessary()

#======= Private Methods =======#

    def _still_matches(self):
        """
        Returns true if the test still corresponds to the structure of the
        problem
        """

        # if there are no longer the same number, not a match.
        if not(len(self.responses) == len(self.capa_problem().responders)):  # pylint: disable=E1101
            return False

        # loop through response models, and check that they match
        all_match = True
        for resp_model in self.responses:  # pylint: disable=E1101
            if not resp_model.still_matches():
                all_match = False
                break

        return all_match

    def _reassign_hashes_if_necessary(self):
        """
        Iterate through the response models, and rematch their
        xml_string and xml_hashes if they have changed in the capa problem
        """

        for response in self.responses:
            response.rematch(response.capa_response)

    def _rematch(self):
        """
        Corrects structure to reflect the state of the capa problem.

        The algorithm proceeds by looking at all possible parings from the two lists
        and calculating the closeness value of the match.  It then begins popping off
        the closest matches and making the match if the clioseness is above some
        threshold value (assuming that neither object has been involved
        in any previous (and therefore better) matches).
        """

        # how desperate are we to make matches?
        cutoff = 0.90

        # copy lists
        unmatched_models = list(self.responses)
        unmatched_responders = list(self.capa_problem().responders.values())

        # make a sorted list of triples of all possible matches and their closeness value
        potential_matches = sorted([(closeness(model, responder), model, responder) for model in unmatched_models for responder in unmatched_responders])

        while potential_matches:
            match = potential_matches.pop()

            # interpret the tuple
            percent_match = match[0]
            model = match[1]
            responder = match[2]

            # if it is not good enought of a match, just stop
            if percent_match < cutoff:
                break

            # only make the match if neither object has been matched
            elif (model in unmatched_models) and (responder in unmatched_responders):

                # make the match and mark as used
                model.rematch(responder)
                unmatched_models.remove(model)
                unmatched_responders.remove(responder)

        # delete unused models
        for model in unmatched_models:
            self.responses.remove(model)

        # create new models for unmatched responders
        for responder in unmatched_responders:
            self._create_child(responder)

        # remake dict
        self._remake_dict_from_children()

    def _evaluate(self, response_dict):
        """
        Give the capa_problem() the response dictionary and return the result
        """

        # instantiate the capa problem so it can grade itself
        capa = self.capa_problem()

        try:
            correct_map = capa.grade_answers(response_dict)
            return correct_map.get_dict()

        # if there is any error, we just return None
        except Exception as e:  # pylint: disable=W0703

            # log the error message
            self.message = str(e)
            return None

    def _make_verdict(self, grade_dict):
        """
        compare what the result of the grading should be with the actual grading
        and return the verdict
        """

        # if there was an error
        if grade_dict is None:
            # if we want error, return pass
            if self.should_be == self.SHOULD_BE["error"]:
                return self.PASS
            return self.ERROR

        # see that they all are the expected value (if not blank)
        passing = True
        for response in self.responses:
            passing = passing and (response.passing(self.should_be, grade_dict))

        if passing:
            return self.PASS
        else:
            return self.FAIL

    def _remake_dict_from_children(self):
        """
        build the response dictionary by getting the values from the children
        """

        # refetch the answers from all the children
        resp_dict = {}
        for response in self.responses:
            resp_dict.update(response.dict_slice())

        # update the dictionary
        self.response_dict = resp_dict

    def _create_children(self):
        """
        create child responses and input entries
        """

        # the first time loaded, we make the responses from
        # the capa moudle
        if self.responses is None:
            self.responses = []
            # create a preview capa problem
            problem_capa = self.capa_problem()

            # go through responder objects
            for responder in problem_capa.responders.itervalues():
                self._create_child(responder, self.response_dict)

            # if the dictionary was incomplete, we remake it so we
            # have all the blank entries.
            self._remake_dict_from_children()

        # else, we just instantiate from the saved versions
        else:
            self.responses = [ResponseTest(**dict(resp_test_dict, content_test=self, response_dict=self.response_dict)) for resp_test_dict in self.responses]

    def _create_child(self, responder, response_dict=dict()):
        """
        from a responder object, create the associated child response model
        """

        self.responses.append(ResponseTest(self, responder.id, etree.tostring(responder.xml), response_dict))


class ResponseTest(object):
    """
    Object that corresponds to the <_____response> fields
    """

    def __init__(self, content_test, string_id, xml_string, response_dict={}, inputs=None):
        """
        To instantiate the response sub-object of a contentTest, we use the following
        - content_test  -- parent object
        - string_id     -- id for the response
        - xml_string    -- string xml definition of the response
        """

        self.content_test = content_test
        self.string_id = string_id
        self.xml_string = xml_string
        self.inputs = inputs

        # we store hashes of various properties about the xml for faster future processing
        self.structure_hash = hash_xml_structure(etree.XML(self.xml_string))
        self.xml_hash = hash_xml(etree.XML(self.xml_string))

        # store the inputs keyd by their order in this response
        if self.inputs is None:
            self.inputs = dict()
            for entry in self.capa_response.inputfields:
                answer = response_dict.get(entry.attrib['id'], '')
                self.inputs[entry.attrib['answer_id']] = {'id': entry.attrib['id'], 'answer': answer}

    def rematch(self, responder):
        """
        reassociates the ids with this new responder object.
        If the hashes match, then all that needs
        changing are the ids. If not, we recalculate hashes.
        (It is assumed that structure_hash's match).

        Note: structure hash is never changed.
        """

        # if the ids and hashes match, we are done
        if self.string_id == responder.id:
            if self.xml_hash == hash_xml(responder.xml):
                return

            # if just the hashes don't match,
            # only update the response model
            # (not the children)
            else:
                self.xml_string = etree.tostring(responder.xml)
                self.xml_hash = hash_xml(responder.xml)
                return

        # The id's don't match, so we re-associate them
        self.string_id = responder.id

        # rematch xml if necessary
        if self.xml_hash != hash_xml(responder.xml):
            self.xml_string = etree.tostring(responder.xml)
            self.xml_hash = hash_xml(responder.xml)

        # rematch all the childrens ids
        for entry in responder.inputfields:

            # reassign the other ids
            index = entry.attrib['answer_id']
            new_id = entry.attrib['id']
            self.inputs[index]['id'] = new_id

    @property
    def capa_response(self):
        """
        get the capa-response object to which this response model corresponds
        """

        parent_capa = self.content_test.capa_problem()  # pylint: disable=E1101
        self_capa = parent_capa.responders_by_id[self.string_id]

        return self_capa

    def still_matches(self):
        """
        check that the model has the same structure as corresponding responder object
        """

        try:
            return self.structure_hash == hash_xml_structure(self.capa_response.xml)
        except KeyError:
            return False

    def dict_slice(self):
        """
        Returns the slice of the total response_dict that this response contains.
        """

        dict_slice = {}

        for entry in self.inputs.values():
            dict_slice[entry['id']] = entry['answer']

        return dict_slice

    def passing(self, should_be, grade_dict):
        """
        For each response whose answer isn't blank, the grade in `grade_dict`
        must be `should_be`
        """

        passes = True
        for entry in self.inputs.values():
            if entry['answer'] != '':
                passes = passes and (grade_dict[entry['id']]['correctness'].lower() == should_be.lower())

        return passes

    def todict(self):
        """
        Serializes object to dictionary
        """

        return {
            "string_id": self.string_id,
            "xml_string": self.xml_string,
            "inputs": self.inputs,
        }
