from nose.tools import assert_equals
from mock import patch

from xmodule.model import *
from xmodule.runtime import *

class Metaclass(NamespacesMetaclass, ParentModelMetaclass, ModelMetaclass):
    pass


class TestNamespace(Namespace):
    n_content = String(scope=Scope.content, default='nc')
    n_settings = String(scope=Scope.settings, default='ns')
    n_student_state = String(scope=Scope.student_state, default='nss')
    n_student_preferences = String(scope=Scope.student_preferences, default='nsp')
    n_student_info = String(scope=Scope.student_info, default='nsi')
    n_by_type = String(scope=Scope(False, ModuleScope.TYPE), default='nbt')
    n_for_all = String(scope=Scope(False, ModuleScope.ALL), default='nfa')
    n_student_def = String(scope=Scope(True, ModuleScope.DEFINITION), default='nsd')


with patch('xmodule.model.Namespace.load_classes', return_value=[('test', TestNamespace)]):
    class TestModel(object):
        __metaclass__ = Metaclass

        content = String(scope=Scope.content, default='c')
        settings = String(scope=Scope.settings, default='s')
        student_state = String(scope=Scope.student_state, default='ss')
        student_preferences = String(scope=Scope.student_preferences, default='sp')
        student_info = String(scope=Scope.student_info, default='si')
        by_type = String(scope=Scope(False, ModuleScope.TYPE), default='bt')
        for_all = String(scope=Scope(False, ModuleScope.ALL), default='fa')
        student_def = String(scope=Scope(True, ModuleScope.DEFINITION), default='sd')

        def __init__(self, model_data):
            self._model_data = model_data


class DictKeyValueStore(KeyValueStore):
    def __init__(self):
        self.db = {}

    def get(self, key):
        return self.db[key]

    def set(self, key, value):
        self.db[key] = value

    def delete(self, key):
        del self.db[key]


Usage = namedtuple('Usage', 'id, def_id')


def test_empty():
    tester = TestModel(DbModel(DictKeyValueStore(), TestModel, 's0', Usage('u0', 'd0')))

    for collection in (tester, tester.test):
        for field in collection.fields:
            print "Getting %s from %r" % (field.name, collection)
            assert_equals(field.default, getattr(collection, field.name))
            new_value = 'new ' + field.name
            print "Setting %s to %s on %r" % (field.name, new_value, collection)
            setattr(collection, field.name, new_value)
            print "Checking %s on %r" % (field.name, collection)
            assert_equals(new_value, getattr(collection, field.name))
