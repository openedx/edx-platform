from collections import namedtuple
from .xmodule import XModule

# N.B. it would be nice to make settings a frozen dictionary, and children a frozen list
# to force usages to behave entirely like values
class Usage(namedtuple('Usage', 'id source settings children')):
    __slots__ = ()

    @classmethod
    def create_usage(cls, source):
        #module = xmodule.get_module(source)
        return Usage(
            "UUID",
            "Foo",
            {},
            [],
        )

    def as_json(self):
        json = self._asdict()
        json['children'] = [child.as_json() for child in json['children']]
        return json


def load_usage(usage_tree):
    """
    usage_tree is a nested set of dictionaries with the following keys:

    id: the uuid of the usage
    source: the id and version of the xmodule that this usage is an instance of
    settings: default settings values set by the source xmodule
    children: child usages
    """
    if usage_tree is None:
        return None

    usage_tree['children'] = [load_usage(child) for child in usage_tree['children']]
    return Usage(**usage_tree)


class StructureModule(XModule):

    def __init__(self, *args, **kwargs):
        super(StructureModule, self).__init__(*args, **kwargs)
        self._usage_tree = None

    @property
    def usage_tree(self):
        if self._usage_tree is None:
            self._usage_tree = load_usage(self.content.get('usage_tree', None))
        return self._usage_tree
