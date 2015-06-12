"""
Views for hint management.

Get to these views through courseurl/hint_manager.
For example: https://courses.edx.org/courses/MITx/2.01x/2013_Spring/hint_manager

These views will only be visible if FEATURES['ENABLE_HINTER_INSTRUCTOR_VIEW'] = True
"""

import json
import re

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie

from edxmako.shortcuts import render_to_response, render_to_string

from courseware.courses import get_course_with_access
from courseware.models import XModuleUserStateSummaryField
import courseware.module_render as module_render
import courseware.model_data as model_data
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.exceptions import ItemNotFoundError


@ensure_csrf_cookie
def hint_manager(request, course_id):
    """
    The URL landing function for all calls to the hint manager, both POST and GET.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        course = get_course_with_access(request.user, 'staff', course_key, depth=None)
    except Http404:
        out = 'Sorry, but students are not allowed to access the hint manager!'
        return HttpResponse(out)
    if request.method == 'GET':
        out = get_hints(request, course_key, 'mod_queue')
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
    error_text = switch_dict[request.POST['op']](request, course_key, field)
    if error_text is None:
        error_text = ''
    render_dict = get_hints(request, course_key, field, course=course)
    render_dict.update({'error': error_text})
    rendered_html = render_to_string('instructor/hint_manager_inner.html', render_dict)
    return HttpResponse(json.dumps({'success': True, 'contents': rendered_html}))


def get_hints(request, course_id, field, course=None):  # pylint: disable=unused-argument
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
    # We want to use the course_id to find all matching usage_id's.
    # To do this, just take the school/number part - leave off the classname.
    # FIXME: we need to figure out how to do this with opaque keys
    all_hints = XModuleUserStateSummaryField.objects.filter(
        field_name=field,
        usage_id__regex=re.escape(u'{0.org}/{0.course}'.format(course_id)),
    )
    # big_out_dict[problem id] = [[answer, {pk: [hint, votes]}], sorted by answer]
    # big_out_dict maps a problem id to a list of [answer, hints] pairs, sorted in order of answer.
    big_out_dict = {}
    # id_to name maps a problem id to the name of the problem.
    # id_to_name[problem id] = Display name of problem
    id_to_name = {}

    for hints_by_problem in all_hints:
        hints_by_problem.usage_id = hints_by_problem.usage_id.map_into_course(course_id)
        name = location_to_problem_name(course_id, hints_by_problem.usage_id)
        if name is None:
            continue
        id_to_name[hints_by_problem.usage_id] = name

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

        # Answer list contains [answer, dict_of_hints] pairs.
        answer_list = sorted(json.loads(hints_by_problem.value).items(), key=answer_sorter)
        big_out_dict[hints_by_problem.usage_id] = answer_list

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
        descriptor = modulestore().get_item(loc)
        return descriptor.get_children()[0].display_name
    except ItemNotFoundError:
        # Sometimes, the problem is no longer in the course.  Just
        # don't include said problem.
        return None


def delete_hints(request, course_id, field, course=None):  # pylint: disable=unused-argument
    """
    Deletes the hints specified.

    `request.POST` contains some fields keyed by integers.  Each such field contains a
    [problem_defn_id, answer, pk] tuple.  These tuples specify the hints to be deleted.

    Example `request.POST`:
    {'op': 'delete_hints',
     'field': 'mod_queue',
      1: ['problem_whatever', '42.0', '3'],
      2: ['problem_whatever', '32.5', '12']}
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk = request.POST.getlist(key)
        problem_key = course_id.make_usage_key_from_deprecated_string(problem_id)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        this_problem = XModuleUserStateSummaryField.objects.get(field_name=field, usage_id=problem_key)
        problem_dict = json.loads(this_problem.value)
        del problem_dict[answer][pk]
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()


def change_votes(request, course_id, field, course=None):  # pylint: disable=unused-argument
    """
    Updates the number of votes.

    The numbered fields of `request.POST` contain [problem_id, answer, pk, new_votes] tuples.
    See `delete_hints`.

    Example `request.POST`:
    {'op': 'delete_hints',
     'field': 'mod_queue',
      1: ['problem_whatever', '42.0', '3', 42],
      2: ['problem_whatever', '32.5', '12', 9001]}
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk, new_votes = request.POST.getlist(key)
        problem_key = course_id.make_usage_key_from_deprecated_string(problem_id)
        this_problem = XModuleUserStateSummaryField.objects.get(field_name=field, usage_id=problem_key)
        problem_dict = json.loads(this_problem.value)
        # problem_dict[answer][pk] points to a [hint_text, #votes] pair.
        problem_dict[answer][pk][1] = int(new_votes)
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()


def add_hint(request, course_id, field, course=None):
    """
    Add a new hint.  `request.POST`:
    op
    field
    problem - The problem id
    answer - The answer to which a hint will be added
    hint - The text of the hint
    """

    problem_id = request.POST['problem']
    problem_key = course_id.make_usage_key_from_deprecated_string(problem_id)
    answer = request.POST['answer']
    hint_text = request.POST['hint']

    # Validate the answer.  This requires initializing the xmodules, which
    # is annoying.
    try:
        descriptor = modulestore().get_item(problem_key)
        descriptors = [descriptor]
    except ItemNotFoundError:
        descriptors = []
    field_data_cache = model_data.FieldDataCache(descriptors, course_id, request.user)
    hinter_module = module_render.get_module(
        request.user,
        request,
        problem_key,
        field_data_cache,
        course_id,
        course=course
    )
    if not hinter_module.validate_answer(answer):
        # Invalid answer.  Don't add it to the database, or else the
        # hinter will crash when we encounter it.
        return 'Error - the answer you specified is not properly formatted: ' + str(answer)

    this_problem = XModuleUserStateSummaryField.objects.get(field_name=field, usage_id=problem_key)

    hint_pk_entry = XModuleUserStateSummaryField.objects.get(field_name='hint_pk', usage_id=problem_key)
    this_pk = int(hint_pk_entry.value)
    hint_pk_entry.value = this_pk + 1
    hint_pk_entry.save()

    problem_dict = json.loads(this_problem.value)
    if answer not in problem_dict:
        problem_dict[answer] = {}
    problem_dict[answer][this_pk] = [hint_text, 1]
    this_problem.value = json.dumps(problem_dict)
    this_problem.save()


def approve(request, course_id, field, course=None):  # pylint: disable=unused-argument
    """
    Approve a list of hints, moving them from the mod_queue to the real
    hint list.  POST:
    op, field
    (some number) -> [problem, answer, pk]

    The numbered fields are analogous to those in `delete_hints` and `change_votes`.
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk = request.POST.getlist(key)
        problem_key = course_id.make_usage_key_from_deprecated_string(problem_id)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        problem_in_mod = XModuleUserStateSummaryField.objects.get(field_name=field, usage_id=problem_key)
        problem_dict = json.loads(problem_in_mod.value)
        hint_to_move = problem_dict[answer][pk]
        del problem_dict[answer][pk]
        problem_in_mod.value = json.dumps(problem_dict)
        problem_in_mod.save()

        problem_in_hints = XModuleUserStateSummaryField.objects.get(field_name='hints', usage_id=problem_key)
        problem_dict = json.loads(problem_in_hints.value)
        if answer not in problem_dict:
            problem_dict[answer] = {}
        problem_dict[answer][pk] = hint_to_move
        problem_in_hints.value = json.dumps(problem_dict)
        problem_in_hints.save()
