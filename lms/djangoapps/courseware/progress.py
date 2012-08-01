class completion(object):
    def __init__(self, **d):
        self.dict = dict({'duration_total': 0,
                          'duration_watched': 0,
                          'done': True,
                          'questions_correct': 0,
                          'questions_incorrect': 0,
                          'questions_total': 0})
        if d:
            self.dict.update(d)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __add__(self, other):
        result = dict(self.dict)
        for item in ['duration_total',
                     'duration_watched',
                     'done',
                     'questions_correct',
                     'questions_incorrect',
                     'questions_total']:
            result[item] = result[item] + other.dict[item]
        return completion(**result)

    def __contains__(self, key):
        return key in dict

    def __repr__(self):
        return repr(self.dict)

if __name__ == '__main__':
    dict1 = completion(duration_total=5)
    dict2 = completion(duration_total=7)
    print dict1 + dict2
