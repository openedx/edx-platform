#-----------------------------------------------------------------------------
# class used to store graded responses to CAPA questions
#
# Used by responsetypes and capa_problem

class CorrectMap(object):
    '''
    Stores (correctness, npoints, msg) for each answer_id.
    Behaves as a dict.
    '''
    cmap = {}

    def __init__(self,*args,**kwargs):
        self.set(*args,**kwargs)

    def set(self,answer_id=None,correctness=None,npoints=None,msg=''):
        if answer_id is not None:
            self.cmap[answer_id] = {'correctness': correctness,
                                    'npoints': npoints,
                                    'msg': msg }

    def __repr__(self):
        return repr(self.cmap)

    def get_dict(self):
        '''
        return dict version of self
        '''
        return self.cmap

    def set_dict(self,correct_map):
        '''
        set internal dict to provided correct_map dict
        for graceful migration, if correct_map is a one-level dict, then convert it to the new
        dict of dicts format.
        '''
        if correct_map and not (type(correct_map[correct_map.keys()[0]])==dict):
            for k in self.cmap.keys(): self.cmap.pop(k)				# empty current dict
            for k in correct_map: self.set(k,correct_map[k])			# create new dict entries
        else:
            self.cmap = correct_map

    def is_correct(self,answer_id):
        if answer_id in self.cmap: return self.cmap[answer_id]['correctness'] == 'correct'
        return None

    def get_npoints(self,answer_id):
        if self.is_correct(answer_id):
            npoints = self.cmap[answer_id].get('npoints',1)	# default to 1 point if correct
            return npoints or 1
        return 0						# if not correct, return 0

    def set_property(self,answer_id,property,value):
        if answer_id in self.cmap: self.cmap[answer_id][property] = value
        else: self.cmap[answer_id] = {property:value}

    def get_property(self,answer_id,property,default=None):
        if answer_id in self.cmap: return self.cmap[answer_id].get(property,default)
        return default

    def get_correctness(self,answer_id):
        return self.get_property(answer_id,'correctness')

    def get_msg(self,answer_id):
        return self.get_property(answer_id,'msg','')

    def update(self,other_cmap):
        '''
        Update this CorrectMap with the contents of another CorrectMap
        '''
        if not isinstance(other_cmap,CorrectMap):
            raise Exception('CorrectMap.update called with invalid argument %s' % other_cmap)
        self.cmap.update(other_cmap.get_dict())

    __getitem__ = cmap.__getitem__
    __iter__ = cmap.__iter__
    items = cmap.items
    keys = cmap.keys

    
