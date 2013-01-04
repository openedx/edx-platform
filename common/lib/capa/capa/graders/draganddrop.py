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
        { "image1": "[10, 20]"  },
        { "ant": "[30, 40]"  },
        { "molecule": "[100, 200]"  },
                ]
}
values are (x,y) coordinates of centers of dragged images.
"""

import json
from collections import OrderedDict


class PositionsCompare(list):
    """ Class for comparing positions.

        Args:
                list or string::
                    "abc" - target
                    [10, 20] - list of integers
                    [[10,20], 200] list of list and integer

    """
    def __eq__(self, other):
        """ Compares two arguments.

        Default lists behavior is conversion of string "abc" to  list
        ["a", "b", "c"]. We will use that.

        If self or other is empty - returns False.

        Args:
                self, other: str, unicode, list, int, float

        Returns: bool
        """
        # checks if self or other is not empty list (empty lists  = false)
        if not self or not other:
            return False

        if (isinstance(self[0], (list, int, float)) and
            isinstance(other[0], (list, int, float))):
            return self.coordinate_positions_compare(other)

        elif (isinstance(self[0], (unicode, str)) and
              isinstance(other[0], (unicode, str))):
            return ''.join(self) == ''.join(other)
        else:  # improper argument types: no (float / int or lists of list
            #and float / int pair) or two string / unicode lists pair
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def coordinate_positions_compare(self, other, r=10):
        """ Checks if self is equal to other inside radius of forgiveness
            (default 10 px).

            Args:
                self, other: [x, y] or [[x, y], r], where r is radius of
                             forgiveness;
                             x, y, r: int

            Returns: bool.
        """
        # get max radius of forgiveness
        if isinstance(self[0], list):  # [(x, y), r] case
            r = max(self[1], r)
            x1, y1 = self[0]
        else:
            x1, y1 = self

        if isinstance(other[0], list):  # [(x, y), r] case
            r = max(other[1], r)
            x2, y2 = other[0]
        else:
            x2, y2 = other

        if (x2 - x1) ** 2 + (y2 - y1) ** 2 > r * r:
            return False

        return True


class DragAndDrop(object):
    """ Grader class for drag and drop inputtype.
    """
    def __init__(self):
        self.correct_groups = OrderedDict()  # correct groups from xml
        self.correct_positions = OrderedDict()  # correct positions for comparing
        self.user_groups = OrderedDict()  # will be populated from user answer
        self.user_positions = OrderedDict()  # will be populated from user answer

    def grade(self):
        ''' Grader user answer.

        If use_targets is True - checks if every draggable isplaced on proper
         target.

        If use_targets is False - checks if every draggable is placed on proper
         coordinates within radius of forgiveness (default is 10).

        Returns: bool.
        '''
        for draggable in self.excess_draggables:
            if not self.excess_draggables[draggable]:
                return False  # user answer has more draggables than correct answer

        # Number of draggables in user_groups may be smaller that in
        # correct_groups, that is incorrect.
        for groupname, draggable_ids in self.correct_groups.items():
            if sorted(draggable_ids) != sorted(self.user_groups[groupname]):
                return False

        # Check that in every group, for rule of that group, user positions of
        #every element are equal with correct positions
        for groupname in self.correct_groups:
            rules_executed = 0
            for rule in ('exact', 'anyof'):   # every group has only one rule
                if self.correct_positions[groupname].get(rule, []):
                    rules_executed += 1
                    if not self.compare_positions(
                            self.correct_positions[groupname][rule],
                            self.user_positions[groupname]['user'], flag=rule):
                        return False
            if not rules_executed:  # no correct rules for current group
            # probably xml content mistake - wrong rules names
                return False

        return True

    def compare_positions(self, correct, user, flag):
        """ Compares two lists of positions with flag rules. Order of
        correct/user arguments is matter only in 'anyof' flag.

        Args:
            correst, user: lists of positions

        Returns: True if within rule lists are equal, otherwise False.
        """
        if flag == 'exact':
            for el1, el2 in zip(correct, user):
                if PositionsCompare(el1) != PositionsCompare(el2):
                    return False

        if flag == 'anyof':
            count = 0
            for u_el in user:
                for c_el in correct:
                    if PositionsCompare(u_el) == PositionsCompare(c_el):
                        count += 1
                        break
            if count != len(user):
                return False

        return True

    def populate(self, correct_answer, user_answer):
        """ Populates DragAndDrop variables from user_answer and correct_answer.
        If correct_answer is dict, converts it to list.
        Correct answer in dict form is simpe structure for fast and simple
        grading. Example of corrrect answer dict example::

            correct_answer = {'name4': 't1',
                            'name_with_icon': 't1',
                            '5': 't2',
                            '7':'t2'}

            It is draggable_name: dragable_position mapping.

        Correct answer in list form is designed for complex cases::

        correct_answers = [
        {
        'draggables': ['1', '2', '3', '4', '5', '6'],
        'targets': [
           's_left', 's_right', 's_sigma', 's_sigma_star', 'p_pi_1',  'p_pi_2'],
        'rule': 'anyof'},
        {
        'draggables': ['7', '8', '9', '10'],
        'targets': ['p_left_1', 'p_left_2', 'p_right_1', 'p_right_2'],
        'rule': 'anyof'
        }
                        ]

        Correct answer in list form is list of dicts, and every dict must have
        3 keys: 'draggables', 'targets' and 'rule'. 'Draggables' value is
        list of draggables ids, 'targes' values are list of targets ids, 'rule'
        value is 'exact' or 'anyof'.

        Args:
            user_answer: json
            correct_answer: dict  or list

        Returns: None

         """
        # convert from dict answer format to list format
        if isinstance(correct_answer, dict):
            tmp = []
            for key, value in correct_answer.items():
                tmp_dict = {'draggables': [], 'targets': [], 'rule': 'exact'}
                tmp_dict['draggables'].append(key)
                tmp_dict['targets'].append(value)
                tmp.append(tmp_dict)
            correct_answer = tmp

        user_answer = json.loads(user_answer)
        self.use_targets = user_answer.get('use_targets')

        # check if we have draggables that are not in correct answer:
        self.excess_draggables = {}

        # create identical data structures from user answer and correct answer
        for i in xrange(0, len(correct_answer)):
            groupname = str(i)
            self.correct_groups[groupname] = correct_answer[i]['draggables']
            self.correct_positions[groupname] = {correct_answer[i]['rule']:
                                                correct_answer[i]['targets']}
            self.user_groups[groupname] = []
            self.user_positions[groupname] = {'user': []}
            for draggable_dict in user_answer['draggables']:
                # draggable_dict is 1-to-1 {draggable_name: position}
                draggable_name = draggable_dict.keys()[0]
                if draggable_name in self.correct_groups[groupname]:
                    self.user_groups[groupname].append(draggable_name)
                    self.user_positions[groupname]['user'].append(
                                            draggable_dict[draggable_name])
                    self.excess_draggables[draggable_name] = True
                else:
                    self.excess_draggables[draggable_name] = \
                    self.excess_draggables.get(draggable_name, False)


def grade(user_input, correct_answer):
    """ Populates DragAndDrop instance from user_input and correct_answer and
        calls DragAndDrop.drade for grading.

        Supports two interfaces for correct_answer: dict and list.

        Args:
            user_input: json. Format::

                {"use_targets": false, "draggables":
                [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'

                or

                {"use_targets": true, "draggables": [{"1": "t1"}, \
                {"name_with_icon": "t2"}]}

            correct_answer: dict or list.

                Dict form::

                        {'1': 't1',  'name_with_icon': 't2'}

                        or

                        {'1': '[10, 10]',  'name_with_icon': '[[10, 10], 20]'}

                List form::

                    correct_answer = [
                    {
                        'draggables':  ['l3_o', 'l10_o'],
                        'targets':  ['t1_o', 't9_o'],
                        'rule': 'anyof'
                    },
                    {
                        'draggables': ['l1_c','l8_c'],
                        'targets': ['t5_c','t6_c'],
                        'rule': 'anyof'
                    }
                    ]

        Returns: bool
    """
    dnd = DragAndDrop()
    dnd.populate(correct_answer=correct_answer, user_answer=user_input)
    return dnd.grade()
