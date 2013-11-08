"""
View assertion functions for XModules
"""

from __future__ import absolute_import

from nose.tools import assert_equals, assert_not_equals  # pylint: disable=no-name-in-module

from xmodule.timelimit_module import TimeLimitModule, TimeLimitDescriptor

from xmodule.tests.rendering.core import assert_student_view_valid_html, assert_student_view_invalid_html


@assert_student_view_valid_html.register(TimeLimitModule)
@assert_student_view_valid_html.register(TimeLimitDescriptor)
def _(block, html):
    """
    Assert that a TimeLimitModule renders student_view html correctly
    """
    assert_not_equals(0, block.get_display_items())
    assert_student_view_valid_html(block.get_children()[0], html)


@assert_student_view_invalid_html.register(TimeLimitModule)
@assert_student_view_invalid_html.register(TimeLimitDescriptor)
def _(block, html):
    """
    Assert that a TimeLimitModule renders student_view html correctly
    """
    assert_equals(0, len(block.get_display_items()))
    assert_equals(u"", html)
