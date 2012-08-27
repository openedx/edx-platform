#-----------------------------------------------------------------------------
# class used to store graded responses to CAPA questions
#
# Used by responsetypes and capa_problem


class CorrectMap(object):
    '''
    Stores map between answer_id and response evaluation result for each question
    in a capa problem.  The response evaluation result for each answer_id includes
    (correctness, npoints, msg, hint, hintmode).

    - correctness : either 'correct' or 'incorrect'
    - npoints     : None, or integer specifying number of points awarded for this answer_id
    - msg         : string (may have HTML) giving extra message response (displayed below textline or textbox)
    - hint        : string (may have HTML) giving optional hint (displayed below textline or textbox, above msg)
    - hintmode    : one of (None,'on_request','always') criteria for displaying hint
    - queuekey    : a random integer for xqueue_callback verification

    Behaves as a dict.
    '''
    def __init__(self, *args, **kwargs):
        self.cmap = dict()		# start with empty dict
        self.items = self.cmap.items
        self.keys = self.cmap.keys
        self.set(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        return self.cmap.__getitem__(*args, **kwargs)

    def __iter__(self):
        return self.cmap.__iter__()

    def set(self, answer_id=None, correctness=None, npoints=None, msg='', hint='', hintmode=None, queuekey=None):
        if answer_id is not None:
            self.cmap[answer_id] = {'correctness': correctness,
                                    'npoints': npoints,
                                    'msg': msg,
                                    'hint': hint,
                                    'hintmode': hintmode,
                                    'queuekey': queuekey,
                                    }

    def __repr__(self):
        return repr(self.cmap)

    def get_dict(self):
        '''
        return dict version of self
        '''
        return self.cmap

    def set_dict(self, correct_map):
        '''
        set internal dict to provided correct_map dict
        for graceful migration, if correct_map is a one-level dict, then convert it to the new
        dict of dicts format.
        '''
        if correct_map and not (type(correct_map[correct_map.keys()[0]]) == dict):
            self.__init__()							# empty current dict
            for k in correct_map: self.set(k, correct_map[k])			# create new dict entries
        else:
            self.cmap = correct_map

    def is_correct(self, answer_id):
        if answer_id in self.cmap: return self.cmap[answer_id]['correctness'] == 'correct'
        return None

    def is_queued(self, answer_id):
        return answer_id in self.cmap and self.cmap[answer_id]['queuekey'] is not None

    def is_right_queuekey(self, answer_id, test_key):
        return answer_id in self.cmap and self.cmap[answer_id]['queuekey'] == test_key

    def get_npoints(self, answer_id):
        npoints = self.get_property(answer_id, 'npoints')
        if npoints is not None:
            return npoints
        elif self.is_correct(answer_id):
            return 1
        return 0 # if not correct and no points have been assigned, return 0

    def set_property(self, answer_id, property, value):
        if answer_id in self.cmap: self.cmap[answer_id][property] = value
        else: self.cmap[answer_id] = {property: value}

    def get_property(self, answer_id, property, default=None):
        if answer_id in self.cmap: return self.cmap[answer_id].get(property, default)
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
        '''
          - hint     : (string) HTML text for hint
          - hintmode : (string) mode for hint display ('always' or 'on_request')
        '''
        self.set_property(answer_id, 'hint', hint)
        self.set_property(answer_id, 'hintmode', hintmode)

    def update(self, other_cmap):
        '''
        Update this CorrectMap with the contents of another CorrectMap
        '''
        if not isinstance(other_cmap, CorrectMap):
            raise Exception('CorrectMap.update called with invalid argument %s' % other_cmap)
        self.cmap.update(other_cmap.get_dict())



