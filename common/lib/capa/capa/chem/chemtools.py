from collections import OrderedDict


def vsepr_parse_user_answer(user_input):
    d = OrderedDict(eval(user_input))
    d['atoms'] = OrderedDict(sorted(d['atoms'].items()))
    return d


def vsepr_build_correct_answer(geometry, atoms):
    correct_answer = OrderedDict()
    correct_answer['geometry'] = geometry
    correct_answer['atoms'] = OrderedDict(atoms)
    return correct_answer


def vsepr_grade(user_input, correct_answer):
    print user_input, type(user_input)
    print correct_answer, type(correct_answer)
    if user_input['geometry'] != correct_answer['geometry']:
        return False
    if user_input['atoms'].values() != correct_answer['atoms'].values():
        return False
    return True

