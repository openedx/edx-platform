"""
Tests for the plugins.i18n_api module.
"""

from unittest.mock import patch

from ..i18n_api import (
    ArgparseArgument,
    atlas_pull_by_modules,
)


def test_argparse_argument():
    """
    Test the ArgparseArgument utility class.
    """
    argument = ArgparseArgument(
        flag="--filter",
        dest="filter",
        help="Some filter",
    )

    assert argument.get_kwargs() == {
        "dest": "filter",
        "help": "Some filter",
    }, 'Should not include `flag` in keyword arguments to match argparse add_argument method'

    assert argument.get_args() == ['--filter'], '--filter should be a positional argument'


def test_atlas_pull_by_modules():
    """
    Test the atlas_pull_by_modules's subprocess.run parameters.
    """
    module_names = ['done', 'drag_and_drop_v2']
    locale_root = '/tmp/locale'

    with patch('subprocess.run') as mock_run:
        atlas_pull_by_modules(module_names, locale_root, ['--filter', 'ar,jp_JP', '--silent'])

    mock_run.assert_called_once_with(
        args=[
            'atlas', 'pull',
            '--expand-glob',
            '--filter', 'ar,jp_JP',
            '--silent',
            'translations/*/done/conf/locale:done',
            'translations/*/drag_and_drop_v2/conf/locale:drag_and_drop_v2',
        ],
        check=True,
        cwd=locale_root,
    )
