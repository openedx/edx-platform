import datetime

from xmodule.model import Namespace, Boolean, Scope, ModelType, String


class DateTuple(ModelType):
    """
    ModelType that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value)

    def to_json(self, value):
        return list(value.timetuple())


class CmsNamespace(Namespace):
    is_draft = Boolean(help="Whether this module is a draft", default=False, scope=Scope.settings)
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = String(help="Id of the user who published this module", scope=Scope.settings)
