from fs.errors import ResourceNotFoundError
import logging
from lxml import etree
import requests
import time
import hashlib

from .util.decorators import lazyproperty
from .graders import load_grading_policy
from .modulestore import Location
from .timeparse import parse_time, stringify_time
from .structure_module import StructureModule
from .xmodule import Plugin

log = logging.getLogger(__name__)


def load_policies(policy_list):
    """
    policy_list is a list of dictionaries, each with the following keys:

    class: The name of a registered policy plugin
    condition: An optional dictionary contaning the optional keys:
        ids: A list of user ids for whom this policy should be applied
        roles: A list of user roles for whom this policy should be applied
    args: An option dictionary containing named arguments to pass to the policy plugin
    """
    return [
        Policy.load_class(policy['class'])(condition=policy.get('condition'), **policy.get('params', {}))
        for policy in policy_list
    ]


class CourseModule(StructureModule):

    @property
    def policies(self):
        return load_policies(self.content.get('policy_list', []))

    def apply_policies(self, user):
        # N.B. this code needs to be expanded to handle policies that are
        # time specific and thus return an expire header
        policies_to_apply = [
            policy
            for policy in self.policies
            if policy.applies_to(user)
        ]

        cache_key = self.cache_id(policies_to_apply)

        cached_tree = self.runtime.cache('policy').get(cache_key)

        if cached_tree is not None:
            return cached_tree

        tree = self.usage_tree

        for policy in policies_to_apply:
            tree = policy.apply(tree)

        self.runtime.cache('policy').set(cache_key, tree)
        return tree

    def cache_id(self, policies):
        hasher = hashlib.md5(str(self.usage_tree.as_json()))
        for policy in policies:
            hasher.update(policy.id)
        return hasher.hexdigest()


class Policy(Plugin):
    entry_point = 'policy.v1'

    def __init__(self, condition):
        self.condition = condition
        self.id =  str(id(self))

    def apply(self, tree):
        return tree

    def applies_to(self, user):
        if self.condition is None:
            return True

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
    def __init__(self, keys, *args, **kwargs):
        super(CascadeKeys, self).__init__(*args, **kwargs)

        self.keys = keys

    def apply(self, tree):
        def cascade(settings):
            new_settings = dict(settings)
            for key in self.keys:
                if key not in new_settings and key in tree.settings:
                    new_settings[key] = tree.settings[key]
            return new_settings

        children = [
            self.apply(child._replace(settings=cascade(child.settings)))
            for child in tree.children
        ]

        return tree._replace(children=children)

class Reschedule(Policy):
    """
    This policy adds a specified timedelta to all start_dates
    """

    def __init__(self, delta, *args, **kwargs):
        super(CascadeKeys, self).__init__(*args, **kwargs)

        self.delta = delta

    def apply(self, tree):
        children = [
            self.apply(child) for child in tree.children
        ]

        settings = dict(tree.settings)
        if 'start_date' in settings:
            settings['start_date'] = settings['start_date'] + delta

        return tree._replace(settings=settings, children=children)

if 0:
    class AppendModule(QueryPolicy):
        """
        This module will append a policy after each module matching the query.
        Any keys in policy_to_copy will be copied from the usage node that
        matches the query.
        """

        def __init__(self, query, source, policy_to_copy=None, *args, **kwargs):
            super(AppendModule, self).__init__(query, *args, **kwargs)
            self.policy_to_copy = policy_to_copy if policy_to_copy is not None else []
            self.source = source

        def update(usage):
            """
            Return a list of usages to replace the returned usage with
            """
            to_insert = Usage.create_usage(self.source)
            policy = dict(to_insert.policy)
            for key in self.policy_to_copy:
                if key in usage:
                    policy[key] = usage[key]

            return [usage, to_insert._replace(policy=policy)] 



