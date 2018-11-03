"""Tests of the xblock.internal module."""

from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import six

from xblock.internal import class_lazy, NamedAttributesMetaclass, Nameable


class TestLazyClassProperty(TestCase):
    """
    Tests of @class_lazy.
    """
    class Base(object):
        """Test class that uses @class_lazy."""
        @class_lazy
        def isolated_dict(cls):  # pylint: disable=no-self-argument
            "Return a different dict for each subclass."
            return {}

    class Derived(Base):
        """Test class that inherits a @class_lazy definition."""
        pass

    def test_isolation(self):
        self.assertEqual({}, self.Base.isolated_dict)
        self.assertEqual({}, self.Derived.isolated_dict)
        self.assertIsNot(self.Base.isolated_dict, self.Derived.isolated_dict)


class TestDescriptor(Nameable):
    """Descriptor that returns itself for introspection in tests."""
    def __get__(self, instance, owner):
        return self


class TestGetSetDescriptor(Nameable):
    """Descriptor that returns itself for introspection in tests."""
    def __get__(self, instance, owner):
        return self

    def __set__(self, instance, value):
        pass


class NamingTester(six.with_metaclass(NamedAttributesMetaclass, object)):
    """Class with several descriptors that should get names."""

    test_descriptor = TestDescriptor()
    test_getset_descriptor = TestGetSetDescriptor()
    test_nonnameable = object()

    def meth(self):
        "An empty method."
        pass

    @property
    def prop(self):
        "An empty property."
        pass


class InheritedNamingTester(NamingTester):
    """Class with several inherited descriptors that should get names."""
    inherited = TestDescriptor()


class TestNamedDescriptorsMetaclass(TestCase):
    "Tests of the NamedDescriptorsMetaclass."

    def test_named_descriptor(self):
        self.assertEqual('test_descriptor', NamingTester.test_descriptor.__name__)

    def test_named_getset_descriptor(self):
        self.assertEqual('test_getset_descriptor', NamingTester.test_getset_descriptor.__name__)

    def test_inherited_naming(self):
        self.assertEqual('test_descriptor', InheritedNamingTester.test_descriptor.__name__)
        self.assertEqual('inherited', InheritedNamingTester.inherited.__name__)

    def test_unnamed_attribute(self):
        self.assertFalse(hasattr(NamingTester.test_nonnameable, '__name__'))

    def test_method(self):
        self.assertEqual('meth', NamingTester.meth.__name__)

    def test_prop(self):
        self.assertFalse(hasattr(NamingTester.prop, '__name__'))
