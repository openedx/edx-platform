"""
Tests outwardly observable behaviour of fields

This test suite attempts to cover the interactions between several
orthogonal attributes that affect the behaviour of xblock fields.

1) Whether the field is mutable or immutable
2) Whether the field is in one of 3 different states
    a) The field has no stored value
        i) The default is statically defined on the field
        ii) The default is computed by the field_data
    b) The field has a stored value
3) Whether we are using the block first vs field first versions of the
   accessors (block.field vs field.read_from(block))

In addition, all of the test cases should behave the same in the
presence of certain preceding noop operations (such as reading the
field from the block, or saving the block before any changes have
been made)

In order to make sure that all of the possible combinations have been
covered, we define sets of test properties (which actually implement the
tests of the various operations), and test setup (which set up the
particular combination of initial conditions that we want to test)
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import copy

from mock import Mock, patch
import six

from xblock.core import XBlock
from xblock.fields import Integer, List, String, ScopeIds, UNIQUE_ID
from xblock.field_data import DictFieldData

from xblock.test.tools import TestRuntime

# Ignore statements that 'have no effect', since the effect is to read
# from the descriptor
# pylint: disable=W0104


# Allow base classes to leave out class attributes and that they access
# without pylint complaining
# pylint: disable=no-member
# ~~~~~~~~~~~~~ Classes defining test operations ~~~~~~~~~~~~~~~~~~~~~~
class BlockFirstOperations(object):
    """
    Defines operations using the block-first implementations

    Requires from subclasses:
        self.block  # An xblock to operate on, which has a field `field`
    """

    def get(self):
        """Retrieve the field from the block"""
        return self.block.field

    def set(self, value):
        """Set the field on the block"""
        self.block.field = value

    def delete(self):
        """Unset the field from the block"""
        del self.block.field

    def is_default(self):
        """Return if the field is set on the block"""
        return not self.block.__class__.field.is_set_on(self.block)


class FieldFirstOperations(object):
    """
    Defines operations using the field-first implementations

    Requires from subclasses:
        self.block  # An xblock to operate on, which has a field `field`
    """

    def get(self):
        """Retrieve the field from the block"""
        return self.block.__class__.field.read_from(self.block)

    def set(self, value):
        """Set the field on the block"""
        self.block.__class__.field.write_to(self.block, value)

    def delete(self):
        """Unset the field from the block"""
        self.block.__class__.field.delete_from(self.block)

    def is_default(self):
        """Return if the field is set on the block"""
        return not self.block.__class__.field.is_set_on(self.block)


# ~~~~~~~~~~~~~ Classes defining test properties ~~~~~~~~~~~~~~~~~~~~~~
class UniversalProperties(object):
    """
    Properties that can be tested without knowing whether a field
    has an initial value or a default value

    Requires from subclasses:
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """

    def test_get_preserves_identity(self):
        first_get = self.get()
        second_get = self.get()

        assert first_get is second_get

    def test_get_with_save_preserves_identity(self):
        first_get = self.get()
        self.block.save()
        second_get = self.get()

        assert first_get is second_get

    def test_set_preserves_identity(self):
        first_get = self.get()
        assert self.new_value is not first_get
        self.set(self.new_value)
        second_get = self.get()

        assert self.new_value is second_get
        assert first_get is not second_get

    def test_set_with_save_preserves_identity(self):
        first_get = self.get()
        self.set(self.new_value)
        self.block.save()
        second_get = self.get()

        assert self.new_value is second_get
        assert first_get is not second_get

    def test_set_with_save_makes_non_default(self):
        self.set(self.new_value)
        self.block.save()
        assert not self.is_default()

    def test_set_without_save_makes_non_default(self):
        self.set(self.new_value)
        assert not self.is_default()

    def test_delete_without_save_writes(self):
        self.delete()
        assert not self.field_data.has(self.block, 'field')
        assert self.is_default()

    def test_delete_with_save_writes(self):
        self.delete()
        self.block.save()
        assert not self.field_data.has(self.block, 'field')
        assert self.is_default()

    def test_set_after_get_always_force_saves(self):
        with patch.object(self.field_data, 'set_many') as patched_set_many:
            self.set(self.get())

            self.block.force_save_fields(['field'])

            patched_set_many.assert_called_with(
                self.block, {'field': self.get()}
            )

    def test_set_after_get_doesnt_save(self):
        with patch.object(self.field_data, 'set_many') as patched_set_many:

            self.set(self.get())
            self.block.save()
            assert not patched_set_many.called

            self.set(self.new_value)
            self.block.save()
            assert patched_set_many.called


class MutationProperties(object):
    """
    Properties of mutable fields that can be tested without knowing
    whether the field has an initial value or a default value

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """

    def test_set_save_get_mutate_save(self):
        reference_value = copy.deepcopy(self.new_value)
        self.mutate(reference_value)

        # Verify that the test isn't vacuously true
        assert self.new_value != reference_value

        self.set(copy.deepcopy(self.new_value))
        self.block.save()
        self.mutate(self.get())
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')
        assert reference_value == final_value

    def test_mutation_with_save_makes_non_default(self):
        self.mutate(self.get())
        self.block.save()
        assert not self.is_default()

    def test_mutation_without_save_makes_non_default(self):
        self.mutate(self.get())
        assert not self.is_default()

    def test_mutate_pointer_after_save(self):
        pointer = self.get()
        self.mutate(pointer)
        self.block.save()
        assert pointer == self.field_data.get(self.block, 'field')

        # now check what happens when we mutate a field
        # that we haven't retrieved through __get__
        # (which would have marked it as dirty)
        self.mutate(pointer)
        self.block.save()
        assert pointer == self.field_data.get(self.block, 'field')

    def test_set_save_mutate_save(self):
        pointer = self.new_value
        self.set(pointer)
        self.block.save()
        self.mutate(pointer)
        self.block.save()
        assert pointer == self.field_data.get(self.block, 'field')


class InitialValueProperties(object):
    """
    Properties dependent on the field having an initial value

    Requires from subclasses:
        self.initial_value: The initial value for the field
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def get_field_data(self):
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldData({'field': copy.deepcopy(self.initial_value)})

    def test_get_gets_initial_value(self):
        assert self.field_data.get(self.block, 'field') == self.get()

    def test_get_with_save_doesnt_write(self):
        initial_value = self.field_data.get(self.block, 'field')
        self.get()
        self.block.save()
        final_value = self.field_data.get(self.block, 'field')

        assert initial_value == final_value

    def test_set_with_save_writes(self):
        initial_value = self.field_data.get(self.block, 'field')
        assert self.new_value is not initial_value
        self.set(self.new_value)
        self.block.save()
        assert self.new_value == self.field_data.get(self.block, 'field')


class DefaultValueProperties(object):
    """
    Properties dependent on the field not having an initial value

    Requires from subclasses:
        self.new_value  # The value to update the field to during testing
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def test_get_with_save_doesnt_write(self):
        assert not self.field_data.has(self.block, 'field')
        self.get()
        self.block.save()
        assert not self.field_data.has(self.block, 'field')

    def test_set_with_save_writes(self):
        assert not self.field_data.has(self.block, 'field')
        self.set(self.new_value)
        self.block.save()
        assert self.new_value == self.field_data.get(self.block, 'field')

    def test_delete_without_save_succeeds(self):
        assert not self.field_data.has(self.block, 'field')

        self.delete()

        assert not self.field_data.has(self.block, 'field')

    def test_delete_with_save_succeeds(self):
        self.delete()
        self.block.save()
        assert not self.field_data.has(self.block, 'field')


class DefaultValueMutationProperties(object):
    """
    Properties testing mutation of default field values

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.block
    """
    def test_mutation_without_save_doesnt_write(self):
        assert not self.field_data.has(self.block, 'field')

        mutable = self.get()
        self.mutate(mutable)

        assert not self.field_data.has(self.block, 'field')

    def test_mutation_with_save_writes(self):
        assert not self.field_data.has(self.block, 'field')

        mutable = self.get()
        reference_copy = copy.deepcopy(mutable)
        self.mutate(reference_copy)

        # Verify that the test isn't vacuously true
        assert mutable != reference_copy

        self.mutate(mutable)
        self.block.save()

        final_value = self.field_data.get(self.block, 'field')
        assert reference_copy == final_value


class InitialValueMutationProperties(object):
    """
    Properties testing mutation of set field value

    Requires from subclasses:
        self.mutate(value)  # Update value in place
        self.block  # An initialized xblock with a field named `field`
        self.field_data  # The field_data used by self.blocks
    """
    def test_mutation_without_save_doesnt_write(self):
        initial_value = self.field_data.get(self.block, 'field')
        reference_copy = copy.deepcopy(initial_value)

        mutable = self.get()
        self.mutate(mutable)

        # Verify that the test isn't vacuously true
        assert reference_copy != mutable

        final_value = self.field_data.get(self.block, 'field')
        assert reference_copy == final_value
        assert initial_value == final_value

    def test_mutation_with_save_writes(self):
        initial_value = self.field_data.get(self.block, 'field')
        reference_copy = copy.deepcopy(initial_value)
        self.mutate(reference_copy)

        # verify that the test isn't vacuously true
        assert initial_value != reference_copy

        mutable = self.get()
        self.mutate(mutable)
        self.block.save()

        final_value = self.field_data.get(self.block, 'field')
        assert reference_copy == final_value


# ~~~~~ Classes linking initial conditions to the properties that test them ~~~~~~
class UniversalTestCases(UniversalProperties):
    """
    Test setup for testing the :class:`~xblock.fields.Field` API

    Requires from subclasses:
        self.field_class  # The class of the field to test
        self.field_default  # The static default value for the field
        self.get_field_data()  # A function that returns a new :class:`~xblock.field_data.FieldData` instance
    """
    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """
        Setup for each test method in the class.
        """
        class TestBlock(XBlock):
            """Testing block for all field API tests"""
            field = self.field_class(default=copy.deepcopy(self.field_default))

        self.field_data = self.get_field_data()
        self.runtime = TestRuntime(services={'field-data': self.field_data})
        self.block = TestBlock(self.runtime, scope_ids=Mock(spec=ScopeIds))
    # pylint: enable=attribute-defined-outside-init


class DictFieldDataWithSequentialDefault(DictFieldData):
    """:class:`~xblock.test.tools.DictFieldData` that generates a sequence of default values"""
    def __init__(self, storage, sequence):
        super(DictFieldDataWithSequentialDefault, self).__init__(storage)
        self._sequence = sequence

    def default(self, block, name):
        return next(iter(self._sequence))


class StaticDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of static default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldData({})


class ComputedDefaultTestCases(UniversalTestCases, DefaultValueProperties):
    """Set up tests of computed default values"""
    def get_field_data(self):
        """Return a new :class:`~xblock.field_data.FieldData` for testing"""
        return DictFieldDataWithSequentialDefault({}, self.default_iterator)


class ImmutableTestCases(UniversalTestCases):
    """Set up tests of an immutable field"""
    field_class = Integer
    field_default = 99
    new_value = 101


class MutableTestCases(UniversalTestCases, MutationProperties):
    """Set up tests of a mutable field"""
    field_class = List
    field_default = []
    new_value = ['a', 'b']

    def mutate(self, value):
        """Modify the supplied value"""
        value.append('foo')


class UniqueIdTestCases(ImmutableTestCases):
    """Set up tests for field with UNIQUE_ID default"""
    field_class = String
    field_default = UNIQUE_ID
    new_value = 'user-assigned ID'
# pylint: enable=no-member


# pylint: disable=C0111
class TestImmutableWithStaticDefault(ImmutableTestCases, StaticDefaultTestCases):
    __test__ = False


class TestImmutableWithUniqueIdDefault(UniqueIdTestCases, StaticDefaultTestCases):
    __test__ = False


class TestImmutableWithComputedDefault(ImmutableTestCases, ComputedDefaultTestCases):
    __test__ = False

    @property
    def default_iterator(self):
        return six.moves.range(1000)


class TestMutableWithStaticDefault(MutableTestCases, StaticDefaultTestCases, DefaultValueMutationProperties):
    __test__ = False


class TestMutableWithInitialValue(MutableTestCases, InitialValueProperties, InitialValueMutationProperties):
    __test__ = False
    initial_value = [1, 2, 3]


class TestMutableWithComputedDefault(MutableTestCases, ComputedDefaultTestCases, DefaultValueMutationProperties):
    __test__ = False

    @property
    def default_iterator(self):
        return ([None] * i for i in six.moves.range(1000))


class TestImmutableWithInitialValue(ImmutableTestCases, InitialValueProperties):
    __test__ = False
    initial_value = 75


class TestImmutableWithInitialValueAndUniqueIdDefault(UniqueIdTestCases, InitialValueProperties):
    __test__ = False
    initial_value = 'initial unique ID'


# ~~~~~~~~~~~~~ Classes for testing noops before other tests ~~~~~~~~~~~~~~~~~~~~

# Allow base classes to leave out class attributes and that they access
# without pylint complaining
# pylint: disable=no-member
class GetNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.field`.

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setup_method(self):
        super(GetNoopPrefix, self).setup_method()
        self.get()


class GetSaveNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.field` and then `self.block.save()`

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setup_method(self):
        super(GetSaveNoopPrefix, self).setup_method()
        self.get()
        self.block.save()


class SaveNoopPrefix(object):
    """
    Mixin that prefixes existing field tests with a call to `self.block.save()`

    This operation is a noop which shouldn't affect whether the tests pass.

    Requires from subclasses:
        self.block  # An initialized xblock with a field named `field`
    """
    def setup_method(self):
        super(SaveNoopPrefix, self).setup_method()
        self.block.save()
# pylint: enable=no-member


for operation_backend in (BlockFirstOperations, FieldFirstOperations):
    for noop_prefix in (None, GetNoopPrefix, GetSaveNoopPrefix, SaveNoopPrefix):
        for base_test_case in (
                TestImmutableWithComputedDefault, TestImmutableWithInitialValue, TestImmutableWithStaticDefault,
                TestMutableWithComputedDefault, TestMutableWithInitialValue, TestMutableWithStaticDefault,
                TestImmutableWithUniqueIdDefault, TestImmutableWithInitialValueAndUniqueIdDefault
        ):

            test_name = base_test_case.__name__ + "With" + operation_backend.__name__
            test_classes = (operation_backend, base_test_case)
            if noop_prefix is not None:
                test_name += "And" + noop_prefix.__name__
                test_classes = (noop_prefix, ) + test_classes

            vars()[test_name] = type(
                str(test_name),  # First argument must be native string type
                test_classes,
                {'__test__': True},
            )

# If we don't delete the loop variables, then they leak into the global namespace
# and cause the last class looped through to be tested twice. Surprise!
# pylint: disable=undefined-loop-variable
del operation_backend
del noop_prefix
del base_test_case
