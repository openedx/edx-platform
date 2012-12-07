from collections import namedtuple

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

        return instance._model_data.get(self.name, self.default)

    def __set__(self, instance, value):
        instance._model_data[self.name] = value

    def __delete__(self, instance):
        del instance._model_data[self.name]

    def __repr__(self):
        return "<{0.__class__.__name} {0.__name__}>".format(self)

    def __lt__(self, other):
        return self._seq < other._seq

Int = Float = Boolean = Object = List = String = Any = ModelType


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Find registered methods
        reg_methods = {}
        for value in attrs.itervalues():
            for reg_type, names in getattr(value, "_method_registrations", {}).iteritems():
                for n in names:
                    reg_methods[reg_type + n] = value
        attrs['registered_methods'] = reg_methods

        if attrs.get('has_children', False):
            attrs['children'] = ModelType(help='The children of this XModule', default=[], scope=None)

            @property
            def child_map(self):
                return dict((child.name, child) for child in self.children)
            attrs['child_map'] = child_map

        fields = []
        for n, v in attrs.items():
            if isinstance(v, ModelType):
                v._name = n
                fields.append(v)
        fields.sort()
        attrs['fields'] = fields

        return super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)
