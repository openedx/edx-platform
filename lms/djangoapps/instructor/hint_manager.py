"""
Views for hint management.

Along with the crowdsource_hinter xmodule, this code is still
experimental, and should not be used in new courses, yet.
"""

import json
import re

from django.http import HttpResponse, Http404
from django_future.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist

from mitxmako.shortcuts import render_to_response, render_to_string

from courseware.courses import get_course_with_access
from courseware.models import XModuleContentField
from courseware.module_render import get_module
from courseware.model_data import ModelDataCache
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore


@ensure_csrf_cookie
def hint_manager(request, course_id):
    try:
        get_course_with_access(request.user, course_id, 'staff', depth=None)
    except Http404:
        out = 'Sorry, but students are not allowed to access the hint manager!'
        return HttpResponse(out)
    if request.method == 'GET':
        out = get_hints(request, course_id, 'mod_queue')
        out.update({'error': ''})
        return render_to_response('instructor/hint_manager.html', out)
    field = request.POST['field']
    if not (field == 'mod_queue' or field == 'hints'):
        # Invalid field.  (Don't let users continue - they may overwrite other db's)
        out = 'Error in hint manager - an invalid field was accessed.'
        return HttpResponse(out)

    switch_dict = {
        'delete hints': delete_hints,
        'switch fields': lambda *args: None,    # Takes any number of arguments, returns None.
        'change votes': change_votes,
        'add hint': add_hint,
        'approve': approve,
    }

    # Do the operation requested, and collect any error messages.
    error_text = switch_dict[request.POST['op']](request, course_id, field)
    if error_text is None:
        error_text = ''
    render_dict = get_hints(request, course_id, field)
    render_dict.update({'error': error_text})
    rendered_html = render_to_string('instructor/hint_manager_inner.html', render_dict)
    return HttpResponse(json.dumps({'success': True, 'contents': rendered_html}))


def get_hints(request, course_id, field):
    """
    Load all of the hints submitted to the course.

    Args:
    `request` -- Django request object.
    `course_id` -- The course id, like 'Me/19.002/test_course'
    `field` -- Either 'hints' or 'mod_queue'; specifies which set of hints to load.

    Keys in returned dict:
        - 'field': Same as input
        - 'other_field': 'mod_queue' if `field` == 'hints'; and vice-versa.
        - 'field_label', 'other_field_label': English name for the above.
        - 'all_hints': A list of [answer, pk dict] pairs, representing all hints.
          Sorted by answer.
        - 'id_to_name': A dictionary mapping problem id to problem name.
    """
    if field == 'mod_queue':
        other_field = 'hints'
        field_label = 'Hints Awaiting Moderation'
        other_field_label = 'Approved Hints'
    elif field == 'hints':
        other_field = 'mod_queue'
        field_label = 'Approved Hints'
        other_field_label = 'Hints Awaiting Moderation'
    # The course_id is of the form school/number/classname.
    # We want to use the course_id to find all matching definition_id's.
    # To do this, just take the school/number part - leave off the classname.
    chopped_id = '/'.join(course_id.split('/')[:-1])
    chopped_id = re.escape(chopped_id)
    all_hints = XModuleContentField.objects.filter(field_name=field, definition_id__regex=chopped_id)
    # big_out_dict[problem id] = [[answer, {pk: [hint, votes]}], sorted by answer]
    # big_out_dict maps a problem id to a list of [answer, hints] pairs, sorted in order of answer.
    big_out_dict = {}
    # id_to name maps a problem id to the name of the problem.
    # id_to_name[problem id] = Display name of problem
    id_to_name = {}

    for hints_by_problem in all_hints:
        loc = Location(hints_by_problem.definition_id)
        name = location_to_problem_name(course_id, loc)
        if name is None:
            continue
        id_to_name[hints_by_problem.definition_id] = name

        def answer_sorter(thing):
            """
            `thing` is a tuple, where `thing[0]` contains an answer, and `thing[1]` contains
            a dict of hints.  This function returns an index based on `thing[0]`, which
            is used as a key to sort the list of things.
            """
            try:
                return float(thing[0])
            except ValueError:
                # Put all non-numerical answers first.
                return float('-inf')

        # Find the signature to answer converter for this problem.  Sometimes,
        # it doesn't exist; just assume that the signatures are the answers.
        try:
            signature_to_ans = XModuleContentField.objects.get(
                field_name='signature_to_ans',
                definition_id__regex=chopped_id
            )
            signature_to_ans = json.loads(signature_to_ans.value)
        except ObjectDoesNotExist:
            signature_to_ans = {}

        signatures_dict = json.loads(hints_by_problem.value)
        unsorted = []
        for signature, dict_of_hints in signatures_dict.items():
            if signature in signature_to_ans:
                ans_txt = signature_to_ans[signature]
            else:   
                ans_txt = signature
            unsorted.append([signature, ans_txt, dict_of_hints])
        # Answer list contains [signature, answer, dict_of_hints] sub-lists.
        answer_list = sorted(unsorted, key=answer_sorter)
        big_out_dict[hints_by_problem.definition_id] = answer_list

    render_dict = {'field': field,
                   'other_field': other_field,
                   'field_label': field_label,
                   'other_field_label': other_field_label,
                   'all_hints': big_out_dict,
                   'id_to_name': id_to_name}
    return render_dict


def location_to_problem_name(course_id, loc):
    """
    Given the location of a crowdsource_hinter module, try to return the name of the
    problem it wraps around.  Return None if the hinter no longer exists.
    """
    try:
        descriptor = modulestore().get_items(loc, course_id=course_id)[0]
        return descriptor.get_children()[0].display_name
    except IndexError:
        # Sometimes, the problem is no longer in the course.  Just
        # don't include said problem.
        return None


def delete_hints(request, course_id, field):
    """
    Deletes the hints specified.

    `request.POST` contains some fields keyed by integers.  Each such field contains a
    [problem_defn_id, signature, pk] tuple.  These tuples specify the hints to be deleted.

    Example `request.POST`:
    {'op': 'delete_hints',
     'field': 'mod_queue',
      1: ['problem_whatever', '42.0', '3'],
      2: ['problem_whatever', '32.5', '12']}
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, signature, pk = request.POST.getlist(key)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        this_problem = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)
        problem_dict = json.loads(this_problem.value)
        del problem_dict[signature][pk]
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()


def change_votes(request, course_id, field):
    """
    Updates the number of votes.

    The numbered fields of `request.POST` contain [problem_id, signature, pk, new_votes] tuples.
    - Very similar to `delete_hints`.  Is there a way to merge them?  Nah, too complicated.
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, signature, pk, new_votes = request.POST.getlist(key)
        this_problem = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)
        problem_dict = json.loads(this_problem.value)
        # problem_dict[signature][pk] points to a [hint_text, #votes] pair.
        problem_dict[signature][pk][1] = int(new_votes)
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()


def add_hint(request, course_id, field):
    """
    Add a new hint.  `request.POST`:
    op
    field
    problem - The problem id
    answer - The answer to which a hint will be added
           - Needs to be converted into signature first.
    hint - The text of the hint
    """

    problem_id = request.POST['problem']
    answer = request.POST['answer']
    hint_text = request.POST['hint']
    this_problem = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)

    hint_pk_entry = XModuleContentField.objects.get(field_name='hint_pk', definition_id=problem_id)
    this_pk = int(hint_pk_entry.value)
    hint_pk_entry.value = this_pk + 1
    hint_pk_entry.save()

    # Make signature.  This is really annoying, but I don't see
    # any alternative :(
    loc = Location(problem_id)
    descriptors = modulestore().get_items(loc)
    m_d_c = ModelDataCache(descriptors, course_id, request.user)
    hinter_module = get_module(request.user, request, loc, m_d_c, course_id)
    signature = hinter_module.answer_signature(answer)
    if signature is None:
        # Signature generation failed.
        # We should probably return an error message, too... working on that.
        return 'Error - your answer could not be parsed as a formula expression.'
    hinter_module.add_signature(signature, answer)

    problem_dict = json.loads(this_problem.value)
    if signature not in problem_dict:
        problem_dict[signature] = {}
    problem_dict[signature][this_pk] = [hint_text, 1]
    this_problem.value = json.dumps(problem_dict)
    this_problem.save()


def approve(request, course_id, field):
    """
    Approve a list of hints, moving them from the mod_queue to the real
    hint list.  POST:
    op, field
    (some number) -> [problem, signature, pk]
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, signature, pk = request.POST.getlist(key)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        problem_in_mod = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)
        problem_dict = json.loads(problem_in_mod.value)
        hint_to_move = problem_dict[signature][pk]
        del problem_dict[signature][pk]
        problem_in_mod.value = json.dumps(problem_dict)
        problem_in_mod.save()

        problem_in_hints = XModuleContentField.objects.get(field_name='hints', definition_id=problem_id)
        problem_dict = json.loads(problem_in_hints.value)
        if signature not in problem_dict:
            problem_dict[signature] = {}
        problem_dict[signature][pk] = hint_to_move
        problem_in_hints.value = json.dumps(problem_dict)
        problem_in_hints.save()
