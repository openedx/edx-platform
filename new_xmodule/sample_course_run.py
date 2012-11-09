
def load_usage(usage_tree):
    """
    usage_tree is a nested set of dictionaries with the following keys:

    id: the uuid of the usage
    source: the id and version of the xmodule that this usage is an instance of
    policy: default policy values set by the source xmodule
    children: usage dictionaries for each child of the source xmodule
    """
    usage_tree['children'] = [load_usage(child) for child in usage_tree['children']]
    return Usage(**usage_tree)

def load_polices(policy_list):
    """
    policy_list is a list of dictionaries, each with the following keys:

    class: The name of a registered policy plugin
    condition: An optional dictionary contaning the optional keys:
        ids: A list of user ids for whom this policy should be applied
        roles: A list of user roles for whom this policy should be applied
    args: An option dictionary containing named arguments to pass to the policy plugin
    """
    return [
        Policy.load_class(policy['class'])(policy.get('condition', {}) **policy.get('args', {}))
        for policy in policy_list
    ]

class Run():
    def __init__(self, id, usage_tree, policy_list):
        """
        id: the id of this course run. Includes a version number
        usage_tree: A Usage that represents the the whole course that this
            run is using
        policy_list: A list of Policy objects
        """
        self.policies = policy_list
        self.usage_tree = Usage(usage_tree)

    def apply_policies(self, user):
        # N.B. this code needs to be expanded to handle policies that are
        # time specific and thus return an expire header
        policies_to_apply = [
            policy
            for policy in self.policies
            if policy.applies_to(user)
        ]

        cache_key = self.cache_id(policies_to_apply)

        cached_tree = policy_cache.get(cache_key)

        if cached_tree is not None:
            return cached_tree

        tree = self.usage_tree

        for policy in policies_to_apply:
            tree = policy.apply(tree)

        policy_cache.set(cache_key, tree)
        return tree

    def cache_id(self, policies):
        hasher = hashlib.md5(self.id)
        for policy in policies:
            hasher.update(policy.id)
        return hasher.hexdigest()


Usage = namedtuple('Usage', 'id source policy children')


class Policy():
    def __init__(self, condition):
        self.condition = condition

    def apply(self, tree):
        return tree

    def applies_to(self, user):
        # N.B. This code may need to expand to allow a more expressive
        # conditional language
        applies_by_id = user.id in self.condition.get('ids', [])
        applies_by_role = bool(set(user.groups) & set(self.condition.get('roles', set())))

        return applies_by_id or applies_by_role


class CascadeKeys(Policy):
    """
    Policy that cascades the values specified for a set of policy keys
    down the tree, prioritizing policies already set on descendents
    over those being cascaded
    """
    def __init__(self, condition, keys):
        super(CascadeKeys, self).__init__(condition)

        self.keys = keys

    def apply(self, tree):
        def cascade(policy):
            new_policy = dict(policy)
            for key in self.keys:
                if key not in new_policy:
                    new_policy[key] = tree[key]
            return new_policy

        children = [
            self.apply(child._update(policy=cascade(child.policy)))
            for child in tree.children
        ]

        return tree._update(children=children)
