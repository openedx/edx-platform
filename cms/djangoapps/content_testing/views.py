"""
Views for using the atuomated content testing feature.  These views should be considered
a mockup for demonstrating the usage of the ContentTest objects.
"""

from django.http import HttpResponse, Http404
from xmodule.modulestore.django import modulestore
from content_testing.models import ContentTest

# csrf utilities because mako.
# Any form submitted with the post methodh should have a hidden input where
# name="csrfmiddlewaretoken" and value = csrf(request)['csrf_token']
# This is not necesary if the form is only used to populate the data of an AJAX call.
from django_future.csrf import ensure_csrf_cookie
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from contentstore.views.access import has_access

from mitxmako.shortcuts import render_to_string
from lxml import etree
from copy import deepcopy

# supported response types
RESPONSE_TYPES = ['customresponse']


def dict_slice(data, string):
    """
    Returns dict of that keys that start with "string" (and removing "string" from the keys)

    This function is used to pull a valid response_dict out of POST data.
    """

    # this can be done beautifully in one line, but pylint complains :(
    d_slice = {}
    for key, value in data.iteritems():
        if key.startswith(string):
            d_slice.update([(key.replace(string, ''), value)])
    return d_slice


@login_required
@ensure_csrf_cookie
def problem_test(request):
    """
    Main routing function for content_testing (and the only one accessible by
    url).

    method == GET       -- Returns summary of tests for this problem, grouped by
        `should_be` values.

    method == POST      --   If `run` is a key in the post data that maps to anything (including
        the empty string), it runs the tests and saves the result.

        Else, it assumes that we are creating a new test, and assumes that the requisite data
        for creating a ContentTest is in the POST datatest to list of tests.

        If an index is amung the post data, it replaces the test at that index instead
        of creating a new one.

    method == DELETE    -- Removes test at index from the list of tests. Index is given in
        in the DELETE data.
    """
    try:
        location = request.GET['location']
    except KeyError:
        try:
            location = request.POST['location']
        except KeyError:
            raise Http404

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    # fetch descriptor once
    descriptor = modulestore().get_item(location)

    if request.method == 'GET':
        html = testing_summary(request, descriptor)
        return HttpResponse('{"html": '+html+'}')

    elif request.method == "POST":
        run = request.POST.get('run', None)
        if run is not None:

            # instantiate
            tests = instantiate_tests(descriptor)

            # run the tests
            for test in tests:
                test.run()

            # update database
            modulestore().update_metadata(location, {'tests': [test.todict() for test in tests]})

        else:
            response_dict = dict_slice(request.POST, 'input_')
            should_be = request.POST['should_be']

            # don't save a blank test
            if any(response_dict.values()):

                # instantiate new test
                new_test = {
                    'location': location,
                    'response_dict': response_dict,
                    'should_be': should_be
                }
                # save
                add_contenttest_to_descriptor(descriptor, new_test)

        return HttpResponse('')

    elif request.method == "DELETE":

        # get necessary data from GET data
        id_to_delete = int(request.GET['id_to_delete'])

        # try to delete
        delete_contenttest(descriptor, id_to_delete)

        return HttpResponse('')


def delete_contenttest(descriptor, id_to_delete):
    """
    Deletes any content test with id `id_to_delete` from the descriptor.  If one
    with that id is not found, raises 404.
    """

    number_tests = len(descriptor.tests)
    new_tests = [test for test in descriptor.tests if not (test['id'] == id_to_delete)]

    # if we didn't find anything, raise 404
    if (len(new_tests) >= number_tests) or (number_tests == 0):
        raise Http404

    # save changes to database
    else:
        modulestore().update_metadata(descriptor.location, {'tests': new_tests})


def add_contenttest_to_descriptor(descriptor, test_dict):
    """
    Adds the test to the descriptor, and creates an id for the test
    """

    tests = descriptor.tests

    # give it an ID one more than the previous one, if there are
    # previou tests
    if tests:
        new_id = tests[-1]['id']+1
    else:
        new_id = 0

    test_dict['id'] = new_id

    # we need to instantiate before saving so rematching will work
    test_dict = ContentTest(**test_dict).todict()

    # add it to the descriptor
    tests.append(test_dict)

    #save it to the database
    modulestore().update_metadata(descriptor.location, {'tests': tests})


def instantiate_tests(descriptor):
    """
    Instantiate the tests of the descriptor such that no db access is needed per test.
    """

    test_dicts = descriptor.tests

    # instantiate preview module (so each test doesn't need to indevidually)
    module = ContentTest.construct_preview_module(descriptor.location)
    tests = [ContentTest(**dict(test_dict, module=module)) for test_dict in test_dicts]

    return tests


def testing_summary(request, descriptor):
    """
    Render the testing summary for this descriptor
    """
    tests = instantiate_tests(descriptor)
    # sort tests by should_be value.
    # The dictionary contains a key for every available `should_be`, and tests are just
    # appended to the value of that key.

    # sorted_tests = {value: [] for value in ContentTest.SHOULD_BE}
    sorted_tests = {}
    for value in ContentTest.SHOULD_BE.values():
        sorted_tests[value] = []
    for test in tests:
        sorted_tests[test.should_be].append(test)

    # for each `should_be` we generate a summary of the tests
    test_summaries = {}
    for should_be in sorted_tests:
        test_summaries[should_be] = render_test_group(request, descriptor, sorted_tests[should_be], should_be)

    # render summaries
    context = {
        'csrf': csrf(request)['csrf_token'],
        'summaries': test_summaries,
        'location': descriptor.location,
    }

    return render_to_string('content_testing/test_summaries.html', context)


def render_test_group(request, descriptor, tests, should_be):
    """
    Render the problem with sections left for the test summaries
    """

    HTML_SIG = '_test_summary'

    # make the lcp
    lcp = ContentTest.construct_preview_module(descriptor.location).lcp

    # generate the summaries for each response
    response_summaries = {}
    for responder in lcp.responders.values():
        response_summaries[responder.id] = aggregate_response_summaries(responder.id, tests)

    section = etree.Element('section')
    tree = deepcopy(lcp.tree)

    for resp in tree.xpath('//' + "|//".join(RESPONSE_TYPES)):
        resp_id = resp.attrib['id']

        # first add what is probably the prompt for the question
        prompt = getprompt(resp)
        if prompt is not None:
            section.append(prompt)

        # construct the summary container
        div = etree.Element('div')
        div.set('class', "response-test-wrapper")
        div.set('id', resp_id+HTML_SIG+'_'+should_be)
        div.extend(response_summaries[resp.attrib['id']])

        # append the create-new form
        form = creation_form(request, descriptor.location, should_be)
        div.append(form)
        form.insert(0, resp)

        section.append(div)

    # use the lcp to render the xml we generated
    lcp.tree = section
    return lcp.get_html()


def getprompt(xml):
    """
    Given an xml object, try to get the xml that looks like it came directly before.
    """

    # try just getting the previous
    prompt = xml.getprevious()

    # if that's none, try the parent (unless that's none too)
    if prompt is None:
        parent = xml.getparent()
        if parent is not None:
            return getprompt(parent)

    return prompt


def aggregate_response_summaries(response_id, tests):
    """
    For tests in the list `tests`, gets all response
    summaries for the response id, and returns the concatenated html summaries.
    """

    # not efficiently searchable :(
    # maybe I should store as dict by id...
    summary = []
    for test in tests:
        for response in test.responses:
            if response.string_id == response_id:

                # only append if the summary is not None
                if response_summary(response, test.message) is not None:
                    summary.append(response_summary(response, test.message))

    return summary


def response_summary(response_test, msg):
    """
    Given response test (child of ContentTest) and overall message of the test,
    returns xml summary
    """

    # sorted list of answers
    answers = [response_test.inputs[index]['answer'] for index in sorted(response_test.inputs)]

    if any(answers):
        context = {
            'msg': msg,
            'answers': answers,
            'id': response_test.content_test.id
        }

        return etree.XML(render_to_string('content_testing/response_summary.html', context))


def creation_form(request, location, should_be):
    """
    Retruns xml form object for creating a new test
    (this needs to be wrapped around the actual rendering of the 
    responder object)
    """

    context = {
        'csrf': csrf(request)['csrf_token'],
        'location': location,
        'should_be': should_be
    }

    return etree.XML(render_to_string('content_testing/test_form.html', context))
