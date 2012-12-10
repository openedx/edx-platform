from collections import namedtuple
from .plugin import Plugin


class ModuleScope(object):
    USAGE, DEFINITION, TYPE, ALL = xrange(4)


class Scope(namedtuple('ScopeBase', 'student module')):
    pass

Scope.content = Scope(student=False, module=ModuleScope.DEFINITION)
Scope.student_state = Scope(student=True, module=ModuleScope.USAGE)
Scope.settings = Scope(student=True, module=ModuleScope.USAGE)
Scope.student_preferences = Scope(student=True, module=ModuleScope.TYPE)
Scope.student_info = Scope(student=True, module=ModuleScope.ALL)


class ModelType(object):
    """
    A field class that can be used as a class attribute to define what data the class will want
    to refer to.

    When the class is instantiated, it will be available as an instance attribute of the same
    name, by proxying through to self._model_data on the containing object.
    """
    sequence = 0

    def __init__(self, help=None, default=None, scope=Scope.content):
        self._seq = self.sequence
        self._name = "unknown"
        self.help = help
        self.default = default
        self.scope = scope
        ModelType.sequence += 1

    @property
    def name(self):
        return self._name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name not in instance._model_data:
            return self.default

        return self.from_json(instance._model_data[self.name])

    def __set__(self, instance, value):
        instance._model_data[self.name] = self.to_json(value)

    def __delete__(self, instance):
        del instance._model_data[self.name]

    def __repr__(self):
        return "<{0.__class__.__name} {0.__name__}>".format(self)

    def __lt__(self, other):
        return self._seq < other._seq

    def to_json(self, value):
        return value

    def from_json(self, value):
        return value

Int = Float = Boolean = Object = List = String = Any = ModelType


class ModelMetaclass(type):
    """
    A metaclass to be used for classes that want to use ModelTypes as class attributes
    to define data access.

    All class attributes that are ModelTypes will be added to the 'fields' attribute on
    the instance.

    Additionally, any namespaces registered in the `xmodule.namespace` will be added to
    the instance
    """
    def __new__(cls, name, bases, attrs):
        fields = []
        for n, v in attrs.items():
            if isinstance(v, ModelType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields

        return super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)


class NamespacesMetaclass(type):
    """
    A metaclass to be used for classes that want to include namespaced fields in their
    instances.

    Any namespaces registered in the `xmodule.namespace` will be added to
    the instance
    """
    def __new__(cls, name, bases, attrs):
        for ns_name, namespace in Namespace.load_classes():
            if issubclass(namespace, Namespace):
                attrs[ns_name] = NamespaceDescriptor(namespace)

        return super(NamespacesMetaclass, cls).__new__(cls, name, bases, attrs)


class ParentModelMetaclass(type):
    """
    A ModelMetaclass that transforms the attribute `has_children = True`
    into a List field with an empty scope.
    """
    def __new__(cls, name, bases, attrs):
        if attrs.get('has_children', False):
            attrs['children'] = List(help='The children of this XModule', default=[], scope=None)
        else:
            attrs['has_children'] = False

        return super(ParentModelMetaclass, cls).__new__(cls, name, bases, attrs)


class NamespaceDescriptor(object):
    def __init__(self, namespace):
        self._namespace = namespace

    def __get__(self, instance, owner):
        if owner is None:
            return self
        return self._namespace(instance)


class Namespace(Plugin):
    """
    A baseclass that sets up machinery for ModelType fields that proxies the contained fields
    requests for _model_data to self._container._model_data.
    """
    __metaclass__ = ModelMetaclass
    __slots__ = ['container']

    entry_point = 'xmodule.namespace'

    def __init__(self, container):
        self._container = container

    @property
    def _model_data(self):
        return self._container._model_data
