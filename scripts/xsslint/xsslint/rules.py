class Rule:
    def __init__(self, rule_id):
        self.rule_id = rule_id

    def __eq__(self, other):
        return self.rule_id == other.rule_id


class RuleSet:
    def __init__(self, **kwargs):
        self.rules = {}
        for k, v in kwargs.items():
            self.rules[k] = Rule(v)

    def __getattr__(self, attr_name):
        return self.rules[attr_name]

    def __add__(self, other):
        result = self.__class__()
        result.rules.update(self.rules)
        result.rules.update(other.rules)
        return result
