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
from collections import OrderedDict


class PositionsCompare(list):
    """Inputs are: "abc" - target
                    [10, 20] - list of integers
                    [[10,20], 200] list of list and integer

    """
    def __eq__(self, other):
        # Default lists behaviour is convers "abc" to ["a", "b", "c"].
        # We will use that.
        # import ipdb; ipdb.set_trace()

        #check if self or other is not empty list (empty lists  = false)
        if not self or not other:
            return False

        # check correct input types
        if (not isinstance(self[0], (str, unicode, list, int)) or
            not isinstance(other[0], (str, unicode, list, int))):
            print 'Incorrect input type'
            return False

        if (isinstance(self[0], (list, int)) and
            isinstance(other[0], (list, int))):
            print 'Numerical position compare'
            return self.coordinate_positions_compare(other)
        elif (isinstance(self[0], (unicode, str)) and
              isinstance(other[0], (unicode, str))):
            print 'Targets compare'
            return ''.join(self) == ''.join(other)
        else:
            # we do not have ints or lists of lists or two string/unicode lists
            # on both sides
            print type(self[0]), type(other[0]), "not correct"
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def coordinate_positions_compare(self, other, r=10):
        """ Checks if pos1 is  equal to pos2 inside radius
        of forgiveness (default 10 px).

            Args:
                self, other: [x, y] or [[x, y], r], where
                             r is radius of forgiveness;
                             x, y, r: int

            Returns: bool.
        """
        print 'I am called',  self, other

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

    def __init__(self):
        self.correct_groups = OrderedDict()  # groups
        self.correct_positions = OrderedDict()  # positions of comparing
        self.user_groups = OrderedDict()
        self.user_positions = OrderedDict()

    def grade(self):
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
                    {'1': '[10, 10]',  'name_with_icon': '[[10, 10], 20]'}

        Returns:
            True or False.
        '''
        if sorted(self.correct_groups.keys()) != sorted(self.user_groups.keys()):
            return False

        for groupname, draggable_ids in self.correct_groups.items():
            if sorted(draggable_ids) != sorted(self.user_groups[groupname]):
                return False

        # from now self.groups and self.user_groups are equal
        assert self.correct_groups == self.user_groups

        # Check fo every group that positions of every group element are equal
        # with positions

        # 'denied' rule
        # import ipdb; ipdb.set_trace()
        denied_positions = [self.correct_positions[g].get('denied', [])
                               for g in self.correct_groups.keys()]
        all_user_positions = [self.user_positions[g]['user']
                                for g in self.correct_groups.keys()]
        if not self.compare_positions(denied_positions,
                                          all_user_positions, flag='denied'):
            return False

        no_exact, no_allowed = False, False
        # 'exact' rule
        for groupname in self.correct_groups:
            if self.correct_positions[groupname].get('exact', []):
                if not self.compare_positions(
                        self.correct_positions[groupname]['exact'],
                        self.user_positions[groupname]['user'], flag='exact'):
                    return False
            else:
                no_exact = True

        # 'allowed' rule
        for groupname in self.correct_groups:
            if self.correct_positions[groupname].get('allowed', []):
                if not self.compare_positions(
                        self.correct_positions[groupname]['allowed'],
                        self.user_positions[groupname]['user'], flag='allowed'):
                    return False
            else:
                no_allowed = True

        if no_allowed and no_exact:
            return False

        return True

    def compare_positions(self, list1, list2, flag):
        # import ipdb; ipdb.set_trace()
        if flag == 'denied':
            for el1 in list1:
                for el2 in list2:
                    if PositionsCompare(el1) == PositionsCompare(el2):
                        return False

        if flag == 'allowed':
            for el1, el2 in zip(sorted(list1), sorted(list2)):
                if PositionsCompare(el1) != PositionsCompare(el2):
                    return False

        if flag == 'exact':
            for el1, el2 in zip(list1, list2):
                if PositionsCompare(el1) != PositionsCompare(el2):
                    return False

        return True

    def populate(self, correct_answer, user_answer):
        """  """

        if isinstance(correct_answer, dict):
            for key, value in correct_answer.items():
                self.correct_groups[key] = [key]
                self.correct_positions[key] = {'exact': [value]}

        user_answer = json.loads(user_answer)
        self.use_targets = user_answer.get('use_targets')

        # create identical data structures
        # user groups must mirror correct_groups
        # and positions  must reflect order in groups

        for groupname in self.correct_groups:
            self.user_groups[groupname] = []
            self.user_positions[groupname] = {'user': []}
            for draggable_dict in user_answer['draggables']:
                # draggable_dict is 1-to-1 {draggable_name: position}
                draggable_name = draggable_dict.keys()[0]
                if draggable_name in self.correct_groups[groupname]:
                    self.user_groups[groupname].append(draggable_name)
                    self.user_positions[groupname]['user'].append(
                                            draggable_dict[draggable_name])

        # import ipdb; ipdb.set_trace()


def grade(user_input, correct_answer):
    """ Support 2 interfaces"""
    if isinstance(correct_answer, dict):
        dnd = DragAndDrop()

    dnd.populate(correct_answer=correct_answer, user_answer=user_input)
    return dnd.grade()
