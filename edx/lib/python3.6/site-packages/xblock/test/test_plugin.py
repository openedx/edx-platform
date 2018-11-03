"""
Test xblock/core/plugin.py
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from mock import patch, Mock
import pytest

from xblock.core import XBlock
from xblock import plugin
from xblock.plugin import AmbiguousPluginError, PluginMissingError


class AmbiguousBlock1(XBlock):
    """A dummy class to find as a plugin."""
    pass


class AmbiguousBlock2(XBlock):
    """A dummy class to find as a plugin."""
    pass


class UnambiguousBlock(XBlock):
    """A dummy class to find as a plugin."""
    pass


@XBlock.register_temp_plugin(AmbiguousBlock1, "bad_block")
@XBlock.register_temp_plugin(AmbiguousBlock2, "bad_block")
@XBlock.register_temp_plugin(UnambiguousBlock, "good_block")
def test_ambiguous_plugins():
    # We can load ok blocks even if there are bad blocks.
    cls = XBlock.load_class("good_block")
    assert cls is UnambiguousBlock

    # Trying to load bad blocks raises an exception.
    expected_msg = (
        "Ambiguous entry points for bad_block: "
        "xblock.test.test_plugin.AmbiguousBlock1, "
        "xblock.test.test_plugin.AmbiguousBlock2"
    )
    with pytest.raises(AmbiguousPluginError, match=expected_msg):
        XBlock.load_class("bad_block")

    # We can use our own function as the select function.
    class MyOwnException(Exception):
        """We'll raise this from `boom`."""
        pass

    def boom(identifier, entry_points):
        """A select function to prove user-defined functions are called."""
        assert len(entry_points) == 2
        assert identifier == "bad_block"
        raise MyOwnException("This is boom")

    with pytest.raises(MyOwnException, match="This is boom"):
        XBlock.load_class("bad_block", select=boom)


def test_nosuch_plugin():
    # We can provide a default class to return for missing plugins.
    cls = XBlock.load_class("nosuch_block", default=UnambiguousBlock)
    assert cls is UnambiguousBlock

    # If we don't provide a default class, an exception is raised.
    with pytest.raises(PluginMissingError, match="nosuch_block"):
        XBlock.load_class("nosuch_block")


@patch.object(XBlock, '_load_class_entry_point', Mock(side_effect=Exception))
def test_broken_plugin():
    plugins = XBlock.load_classes()
    assert list(plugins) == []


def _num_plugins_cached():
    """
    Returns the number of plugins that have been cached.
    """
    return len(plugin.PLUGIN_CACHE)


@XBlock.register_temp_plugin(AmbiguousBlock1, "thumbs")
def test_plugin_caching():
    plugin.PLUGIN_CACHE = {}
    assert _num_plugins_cached() == 0

    XBlock.load_class("thumbs")
    assert _num_plugins_cached() == 1

    XBlock.load_class("thumbs")
    assert _num_plugins_cached() == 1
