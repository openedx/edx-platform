""" Grader of drag and drop input.

Client side behavior: user can drag and drop images from list on base image.
Parameter 'use_targets' in xml can control two use cases.

if use_targets is true (defaut), then json returned from client is:
 {
    "use_targets": true,
    "draggable": [
        { "image1": "t1"  },
        { "ant": "t2"  },
        { "molecule": "t3"  },
                ]
}
values are target names.

If use_targets is false:
 {
    "use_targets": false,
    "draggable": [
        { "image1": "(10, 20)"  },
        { "ant": "(30, 40)"  },
        { "molecule": "(100, 200)"  },
                ]
}
values are (x,y) coordinates of centers of dragged images.

"""

import json


def grade(user_input, correct_answer):
    '''
    Grade drag and drop problem.
    If use_targets is True - checks if image placed on proper target.
    If use_targets is False - checks if image placed on proper coordinates,
    with setted radius of forgiveness (default is 10)

    Args:
        user_input, correct_answer: json. Format:

        user_input: see module docstring

        correct_answer:
            if use_targets is True:
                {'1': 't1',  'name_with_icon': 't2'}
            else:
                {'1': '(10, 10)',  'name_with_icon': '[(10, 10), 20]'}

    Returns:
        True or False.
    '''

    user_answer = json.loads(user_input)

    if len(correct_answer.keys()) != len(user_answer['draggables']):
        return False

    def is_equal(user_answer, correct_answer):
        """ Checks if user_answer is  equal to correct_answer inside radius
        of forgiveness (default 10 px).

            Args:
                user_answer:    [x, y]  - list of floats;
                correct_answer: [x, y] or [[x, y], r], where
                                r is radius of forgiveness;

            Returns: bool.
        """
        if not isinstance(correct_answer, list) or \
           not isinstance(user_answer, list):
            return False

        r = 10
        if isinstance(correct_answer[0], list):  # [(x, y), r] case
            r = correct_answer[1]
            corr_x = correct_answer[0][0]
            corr_y = correct_answer[0][1]
        else:  # (x, y) case
            corr_x = correct_answer[0]
            corr_y = correct_answer[1]

        if ((user_answer[0] - corr_x) ** 2 +
            (user_answer[1] - corr_y) ** 2) > r * r:
            return False

        return True

    if user_answer["use_targets"]:
        is_equal = lambda user, correct: user == correct if (
             isinstance(user, unicode) and isinstance(correct, str)) else False

    for draggable in user_answer['draggables']:
        if not is_equal(draggable.values()[0],
                        correct_answer[draggable.keys()[0]]):
            return False

    return True
