from mock import patch
from unittest import TestCase
from nose.tools import assert_in, assert_equals, assert_raises

from xmodule.model import *


def test_model_metaclass():
    class ModelMetaclassTester(object):
        __metaclass__ = ModelMetaclass

        field_a = Int(scope=Scope.settings)
        field_b = Int(scope=Scope.content)

        def __init__(self, model_data):
            self._model_data = model_data

    assert hasattr(ModelMetaclassTester, 'field_a')
    assert hasattr(ModelMetaclassTester, 'field_b')

    assert_in(ModelMetaclassTester.field_a, ModelMetaclassTester.fields)
    assert_in(ModelMetaclassTester.field_b, ModelMetaclassTester.fields)


def test_parent_metaclass():

    class HasChildren(object):
        __metaclass__ = ParentModelMetaclass

        has_children = True

    class WithoutChildren(object):
        __metaclass = ParentModelMetaclass

    assert hasattr(HasChildren, 'children')
    assert not hasattr(WithoutChildren, 'children')

    assert isinstance(HasChildren.children, List)
    assert_equals(None, HasChildren.children.scope)


def test_field_access():
    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field_a = Int(scope=Scope.settings)
        field_b = Int(scope=Scope.content, default=10)
        field_c = Int(scope=Scope.student_state, computed_default=lambda s: s.field_a + s.field_b)

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({'field_a': 5, 'field_x': 15})

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(15, field_tester.field_c)
    assert not hasattr(field_tester, 'field_x')

    field_tester.field_a = 20
    assert_equals(20, field_tester._model_data['field_a'])
    assert_equals(10, field_tester.field_b)
    assert_equals(30, field_tester.field_c)

    del field_tester.field_a
    assert_equals(None, field_tester.field_a)
    assert hasattr(FieldTester, 'field_a')


class TestNamespace(Namespace):
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.student_state, default="default_value")


@patch('xmodule.model.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_metaclass(mock_load_classes):
    class TestClass(object):
        __metaclass__ = NamespacesMetaclass

    assert hasattr(TestClass, 'test')
    assert hasattr(TestClass.test, 'field_x')
    assert hasattr(TestClass.test, 'field_y')

    assert_in(TestNamespace.field_x, TestClass.test.fields)
    assert_in(TestNamespace.field_y, TestClass.test.fields)
    assert isinstance(TestClass.test, Namespace)


@patch('xmodule.model.Namespace.load_classes', return_value=[('test', TestNamespace)])
def test_namespace_field_access(mock_load_classes):
    class Metaclass(ModelMetaclass, NamespacesMetaclass):
        pass

    class FieldTester(object):
        __metaclass__ = Metaclass

        field_a = Int(scope=Scope.settings)
        field_b = Int(scope=Scope.content, default=10)
        field_c = Int(scope=Scope.student_state, computed_default=lambda s: s.field_a + s.field_b)

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({
        'field_a': 5,
        'field_x': [1, 2, 3],
    })

    assert_equals(5, field_tester.field_a)
    assert_equals(10, field_tester.field_b)
    assert_equals(15, field_tester.field_c)
    assert_equals([1, 2, 3], field_tester.test.field_x)
    assert_equals('default_value', field_tester.test.field_y)

    field_tester.test.field_x = ['a', 'b']
    assert_equals(['a', 'b'], field_tester._model_data['field_x'])

    del field_tester.test.field_x
    assert_equals(None, field_tester.test.field_x)

    assert_raises(AttributeError, getattr, field_tester.test, 'field_z')
    assert_raises(AttributeError, delattr, field_tester.test, 'field_z')

    # Namespaces are created on the fly, so setting a new attribute on one
    # has no long-term effect
    field_tester.test.field_z = 'foo'
    assert_raises(AttributeError, getattr, field_tester.test, 'field_z')
    assert 'field_z' not in field_tester._model_data


def test_field_serialization():

    class CustomField(ModelType):
        def from_json(self, value):
            return value['value']

        def to_json(self, value):
            return {'value': value}

    class FieldTester(object):
        __metaclass__ = ModelMetaclass

        field = CustomField()

        def __init__(self, model_data):
            self._model_data = model_data

    field_tester = FieldTester({
        'field': {'value': 4}
    })

    assert_equals(4, field_tester.field)
    field_tester.field = 5
    assert_equals({'value': 5}, field_tester._model_data['field'])
