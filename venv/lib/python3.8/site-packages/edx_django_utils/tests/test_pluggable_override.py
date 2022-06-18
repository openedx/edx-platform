"""
Tests for utilities.
"""

from django.test import override_settings

from edx_django_utils.plugins import pluggable_override


@pluggable_override('OVERRIDE_TRANSFORM')
def transform(x):
    return x + 10


def decrement(prev_fn, x):
    if x >= 10:
        return x - 1
    else:
        return prev_fn(x) - 1


def double(prev_fn, x):
    if x >= 11:
        return x * 2
    else:
        return prev_fn(x) * 2


def test_no_override():
    """Test that the original function is called when an override is not specified."""
    assert transform(10) == 20


@override_settings(OVERRIDE_TRANSFORM="{}.decrement".format(__name__))
def test_override():
    """Test that the overriding function is called."""
    assert transform(10) == 9


@override_settings(OVERRIDE_TRANSFORM="{}.decrement".format(__name__))
def test_call_original_function():
    """Test that the overriding function calls the base one."""
    assert transform(9) == 18


@override_settings(OVERRIDE_TRANSFORM="{0}.decrement,{0}.double".format(__name__).split(','))
def test_multiple_overrides_call_last_function():
    """Test that the newest (last) overriding function is called when multiple overrides are specified."""
    assert transform(11) == 22


@override_settings(OVERRIDE_TRANSFORM="{0}.decrement,{0}.double".format(__name__).split(','))
def test_multiple_overrides_fallback_to_previous_function():
    """Test that the last overriding function can call the previous one from the chain."""
    assert transform(10) == 18


@override_settings(OVERRIDE_TRANSFORM="{0}.decrement,{0}.double".format(__name__).split(','))
def test_multiple_overrides_fallback_to_base_function():
    """Test that the overriding functions can eventually call the base one."""
    assert transform(9) == 36
