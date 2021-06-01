# -----------------------------------------------------------------------------
# class used to store graded responses to CAPA questions
#
# Used by responsetypes and capa_problem


class CorrectMap(object):
    """
    Stores map between answer_id and response evaluation result for each question
    in a capa problem.  The response evaluation result for each answer_id includes
    (correctness, npoints, msg, hint, hintmode).

    - correctness : 'correct', 'incorrect', 'partially-correct', or 'incomplete'
    - npoints     : None, or integer specifying number of points awarded for this answer_id
    - msg         : string (may have HTML) giving extra message response
                    (displayed below textline or textbox)
    - hint        : string (may have HTML) giving optional hint
                    (displayed below textline or textbox, above msg)
    - hintmode    : one of (None,'on_request','always') criteria for displaying hint
    - queuestate  : Dict {key:'', time:''} where key is a secret string, and time is a string dump
                    of a DateTime object in the format '%Y%m%d%H%M%S'. Is None when not queued

    Behaves as a dict.
    """

    def __init__(self, *args, **kwargs):
        # start with empty dict
        self.cmap = dict()
        self.items = self.cmap.items
        self.keys = self.cmap.keys
        self.overall_message = ""
        self.set(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        return self.cmap.__getitem__(*args, **kwargs)

    def __iter__(self):
        return self.cmap.__iter__()

    # See the documentation for 'set_dict' for the use of kwargs
    def set(
        self,
        answer_id=None,
        correctness=None,
        npoints=None,
        msg='',
        hint='',
        hintmode=None,
        queuestate=None,
        answervariable=None,  # pylint: disable=C0330
        **kwargs
    ):

        if answer_id is not None:
            self.cmap[answer_id] = {
                'correctness': correctness,
                'npoints': npoints,
                'msg': msg,
                'hint': hint,
                'hintmode': hintmode,
                'queuestate': queuestate,
                'answervariable': answervariable,
            }

    def __repr__(self):
        return repr(self.cmap)

    def get_dict(self):
        """
        return dict version of self
        """
        return self.cmap

    def set_dict(self, correct_map):
        """
        Set internal dict of CorrectMap to provided correct_map dict

        correct_map is saved by LMS as a plaintext JSON dump of the correctmap dict. This
        means that when the definition of CorrectMap (e.g. its properties) are altered,
        an existing correct_map dict will not coincide with the newest CorrectMap format as
        defined by self.set.

        For graceful migration, feed the contents of each correct map to self.set, rather than
        making a direct copy of the given correct_map dict. This way, the common keys between
        the incoming correct_map dict and the new CorrectMap instance will be written, while
        mismatched keys will be gracefully ignored.

        Special migration case:
            If correct_map is a one-level dict, then convert it to the new dict of dicts format.

        """
        # empty current dict
        self.__init__()

        if not correct_map:
            return

        # create new dict entries
        if not isinstance(list(correct_map.values())[0], dict):
            # special migration
            for k in correct_map:
                self.set(k, correctness=correct_map[k])
        else:
            for k in correct_map:
                self.set(k, **correct_map[k])

    def is_correct(self, answer_id):
        """
        Takes an answer_id
        Returns true if the problem is correct OR partially correct.
        """
        if answer_id in self.cmap:
            return self.cmap[answer_id]['correctness'] in ['correct', 'partially-correct']
        return None

    def is_partially_correct(self, answer_id):
        """
        Takes an answer_id
        Returns true if the problem is partially correct.
        """
        if answer_id in self.cmap:
            return self.cmap[answer_id]['correctness'] == 'partially-correct'
        return None

    def is_queued(self, answer_id):
        return answer_id in self.cmap and self.cmap[answer_id]['queuestate'] is not None

    def is_right_queuekey(self, answer_id, test_key):
        return self.is_queued(answer_id) and self.cmap[answer_id]['queuestate']['key'] == test_key

    def get_queuetime_str(self, answer_id):
        if self.cmap[answer_id]['queuestate']:
            return self.cmap[answer_id]['queuestate']['time']
        else:
            return None

    def get_npoints(self, answer_id):
        """Return the number of points for an answer, used for partial credit."""
        npoints = self.get_property(answer_id, 'npoints')
        if npoints is not None:
            return npoints
        elif self.is_correct(answer_id):
            return 1
        # if not correct and no points have been assigned, return 0
        return 0

    def set_property(self, answer_id, property, value):
        if answer_id in self.cmap:
            self.cmap[answer_id][property] = value
        else:
            self.cmap[answer_id] = {property: value}

    def get_property(self, answer_id, property, default=None):
        if answer_id in self.cmap:
            return self.cmap[answer_id].get(property, default)
        return default

    def get_correctness(self, answer_id):
        return self.get_property(answer_id, 'correctness')

    def get_msg(self, answer_id):
        return self.get_property(answer_id, 'msg', '')

    def get_hint(self, answer_id):
        return self.get_property(answer_id, 'hint', '')

    def get_hintmode(self, answer_id):
        return self.get_property(answer_id, 'hintmode', None)

    def set_hint_and_mode(self, answer_id, hint, hintmode):
        """
          - hint     : (string) HTML text for hint
          - hintmode : (string) mode for hint display ('always' or 'on_request')
        """
        self.set_property(answer_id, 'hint', hint)
        self.set_property(answer_id, 'hintmode', hintmode)

    def update(self, other_cmap):
        """
        Update this CorrectMap with the contents of another CorrectMap
        """
        if not isinstance(other_cmap, CorrectMap):
            raise Exception('CorrectMap.update called with invalid argument %s' % other_cmap)
        self.cmap.update(other_cmap.get_dict())
        self.set_overall_message(other_cmap.get_overall_message())

    def set_overall_message(self, message_str):
        """ Set a message that applies to the question as a whole,
            rather than to individual inputs. """
        self.overall_message = str(message_str) if message_str else ""

    def get_overall_message(self):
        """ Retrieve a message that applies to the question as a whole.
        If no message is available, returns the empty string """
        return self.overall_message
