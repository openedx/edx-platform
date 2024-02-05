"""
Tests for the plugins.i18n_api Django commands module.
"""
from unittest.mock import patch

from django.core.management import call_command


def test_pull_plugin_translations_command(settings, tmp_path):
    """
    Test the `pull_plugin_translations` Django command.
    """
    plugins_locale_root = tmp_path / 'conf/plugins-locale/plugins'
    plugins_locale_root.mkdir(parents=True)
    settings.REPO_ROOT = tmp_path

    with patch('subprocess.run') as mock_run:
        call_command(
            'pull_plugin_translations',
            verbose=True,
            filter='ar,es_ES',
            repository='custom_repo',
        )

    assert mock_run.call_count == 1, 'Expected to call `subprocess.run` once'
    call_kwargs = mock_run.call_args.kwargs

    assert call_kwargs['check'] is True
    assert call_kwargs['cwd'] == plugins_locale_root
    assert call_kwargs['args'][:8] == [
        'atlas', 'pull', '--expand-glob',
        '--filter', 'ar,es_ES',
        '--repository', 'custom_repo',
        '--verbose'
    ], 'Pass arguments to atlas pull correctly'

    assert 'translations/*/edx_proctoring/conf/locale:edx_proctoring' in call_kwargs['args'], (
        'Pull edx-proctoring translations by Python module name using the "--expand-glob" option'
    )


def test_compile_plugin_translations_command(settings):
    """
    Test the `compile_plugin_translations` Django command.
    """
    with patch('openedx.core.djangoapps.plugins.i18n_api.compile_po_files') as mock_compile_po_files:
        call_command('compile_plugin_translations')

    mock_compile_po_files.assert_called_once_with(settings.REPO_ROOT / 'conf/plugins-locale/plugins')
