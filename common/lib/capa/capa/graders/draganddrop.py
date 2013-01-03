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
        else:  # improper argument types
            # Now we have no (float / int or lists of list and float / int pair)
            # or two string / unicode lists pair
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
    """ Grader for drag and drop inputtype.
    """

    def __init__(self):
        self.correct_groups = OrderedDict()  # correct groups from xml
        self.correct_positions = OrderedDict()  # correct positions for comparing
        self.user_groups = OrderedDict()  # will be populated from user answer
        self.user_positions = OrderedDict()  # will be populated from user answer

        # flag to check if user answer has more draggables than correct answer
        self.incorrect = False

    def grade(self):
        ''' Grader user answer.

        If use_targets is True - checks if every draggable isplaced on proper
         target.

        If use_targets is False - checks if every draggable is placed on proper
         coordinates within radius of forgiveness (default is 10).

        Returns: bool.
        '''

        if self.incorrect:  # user answer has more draggables than correct answer
            return False

        # checks if we have same groups of draggables
        if sorted(self.correct_groups.keys()) != sorted(self.user_groups.keys()):
            return False

        # checks if for every groups draggables names are same
        for groupname, draggable_ids in self.correct_groups.items():
            if sorted(draggable_ids) != sorted(self.user_groups[groupname]):
                return False

        # from now self.correct_groups and self.user_groups are equal if
        # order is ignored

        # Checks in every group that user positions of every element are equal
        # with correct positions for every rule

        # for group in self.correct_groups:  # 'denied' rule
        #     if not self.compare_positions(self.correct_positions[group].get(
        #     'denied', []), self.user_positions[group]['user'], flag='denied'):
        #         return False

        passed_rules = dict()
        for rule in ('exact', 'anyof'):
            passed_rules[rule] = True
            for groupname in self.correct_groups:
                if self.correct_positions[groupname].get(rule, []):
                    if not self.compare_positions(
                            self.correct_positions[groupname][rule],
                            self.user_positions[groupname]['user'], flag=rule):
                        return False
                else:
                    passed_rules[rule] = False

        # if all passed rules are false
        if not reduce(lambda x, y: x or y, passed_rules):
            return False

        return True

    def compare_positions(self, correct, user, flag):
        """ order of correct/user is matter only in anyof_flag"""
        # import ipdb; ipdb.set_trace()
        # if flag == 'denied':
        #     for el1 in correct:
        #         for el2 in user:
        #             if PositionsCompare(el1) == PositionsCompare(el2):
        #                 return False

        # if flag == 'allowed':
        #     for el1, el2 in zip(sorted(correct), sorted(user)):
        #         if PositionsCompare(el1) != PositionsCompare(el2):
        #             return False

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
        """  """
        # convert from dict format to list format
        tmp = []
        if isinstance(correct_answer, dict):
            for key, value in correct_answer.items():
                tmp_dict = {'draggables': [], 'targets': [], 'rule': 'exact'}
                tmp_dict['draggables'].append(key)
                tmp_dict['targets'].append(value)
                tmp.append(tmp_dict)
        correct_answer = tmp

        user_answer = json.loads(user_answer)
        self.use_targets = user_answer.get('use_targets')

        # check if we have draggables that are not in correct answer:
        check_extra_draggables = {}

        # create identical data structures
        # user groups must mirror correct_groups
        # and positions  must reflect order in group
        for i in xrange(0, len(correct_answer)):
            groupname = str(i)
            self.correct_groups = OrderedDict()
            self.correct_groups[groupname] = correct_answer[i]['draggables']
            self.correct_positions = OrderedDict()
            self.correct_positions[groupname] = {correct_answer[i]['rule']: correct_answer[i]['targets']}
            self.user_groups[groupname] = []
            self.user_positions[groupname] = {'user': []}
            for draggable_dict in user_answer['draggables']:
                # draggable_dict is 1-to-1 {draggable_name: position}
                draggable_name = draggable_dict.keys()[0]
                if draggable_name in self.correct_groups[groupname]:
                    self.user_groups[groupname].append(draggable_name)
                    self.user_positions[groupname]['user'].append(
                                            draggable_dict[draggable_name])
                    check_extra_draggables[draggable_name] = True
                else:
                    check_extra_draggables[draggable_name] = \
                    check_extra_draggables.get(draggable_name, False)

        for draggable in check_extra_draggables:
            if not check_extra_draggables[draggable]:
                self.incorrect = True
        # import ipdb; ipdb.set_trace()


def grade(user_input, correct_answer):
    """Args:
            user_input, correct_answer: json. Format:

            user_input: see module docstring

            correct_answer:
                if use_targets is True:
                    {'1': 't1',  'name_with_icon': 't2'}
                else:
                    {'1': '[10, 10]',  'name_with_icon': '[[10, 10], 20]'}
    Support 2 interfaces"""
    dnd = DragAndDrop()
    dnd.populate(correct_answer=correct_answer, user_answer=user_input)
    return dnd.grade()
