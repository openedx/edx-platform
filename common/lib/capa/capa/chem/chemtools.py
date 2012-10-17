from collections import OrderedDict
import json


def vsepr_parse_user_answer(user_input):
    d = OrderedDict(json.loads(user_input))
    d['atoms'] = OrderedDict(sorted(d['atoms'].items()))
    return d


def vsepr_build_correct_answer(geometry, atoms):
    correct_answer = OrderedDict()
    correct_answer['geometry'] = geometry
    correct_answer['atoms'] = OrderedDict(sorted(atoms.items()))
    return correct_answer


def vsepr_grade(user_input, correct_answer, ignore_p_order=False, ignore_a_order=False, ignore_e_order=False):
    """ Flags ignore_(a,p,e)_order are for checking order in axial, perepherial or equatorial positions
    """
    # print user_input, type(user_input)
    # print correct_answer, type(correct_answer)
    if user_input['geometry'] != correct_answer['geometry']:
        return False

    # not order-aware comparisons
    for ignore in [(ignore_p_order, 'p'), (ignore_e_order, 'e'), (ignore_a_order, 'a')]:
        if ignore[0]:
            # collecting atoms:
            a_user = [v for k, v in user_input['atoms'].items() if k.startswith(ignore[1])]
            a_correct = [v for k, v in correct_answer['atoms'].items() if k.startswith(ignore[1])]
            # print ignore[0], ignore[1], a_user, a_correct
            if len(a_user) != len(a_correct):
                return False
            if sorted(a_user) != sorted(a_correct):
                return False

    # order-aware comparisons
    for ignore in [(ignore_p_order, 'p'), (ignore_e_order, 'e'), (ignore_a_order, 'a')]:
        if not ignore[0]:
            # collecting atoms:
            a_user = [v for k, v in user_input['atoms'].items() if k.startswith(ignore[1])]
            a_correct = [v for k, v in correct_answer['atoms'].items() if k.startswith(ignore[1])]
            # print '2nd', ignore[0], ignore[1], a_user, a_correct
            if len(a_user) != len(a_correct):
                return False
            if len(a_correct) == 0:
                continue
            if a_user != a_correct:
                return False

    return True
