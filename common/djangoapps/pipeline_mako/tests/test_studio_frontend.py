"""
Tests for the studiofrontend helper module.
"""

import logging
import os

import pytest

from ..helpers import studiofrontend


def test_messages_file_not_found(tmpdir, settings, caplog):
    """
    Ensure load_sfe_i18n_messages returns an empty json string when the messages file is not found.
    """
    caplog.set_level(logging.INFO)
    settings.REPO_ROOT = tmpdir
    assert studiofrontend.load_sfe_i18n_messages('ar') == '{}'
    assert 'studiofrontend language files for langauge \'ar\' was not found' in caplog.text


def test_messages_file_error(tmpdir, settings, caplog):
    """
    Ensure load_sfe_i18n_messages returns an empty json string when the messages file is not found.
    """
    caplog.set_level(logging.INFO)
    settings.REPO_ROOT = tmpdir
    # create a directory to cause an OSError when attempting to read it as a file
    os.makedirs(tmpdir / 'conf/plugins-locale/studio-frontend/ar.json')
    assert studiofrontend.load_sfe_i18n_messages('ar') == '{}'
    assert 'Error loading studiofrontend language files for langauge' in caplog.text


@pytest.mark.parametrize('language', ['jp-jp', 'jp_JP'])
def test_messages_file_found(tmpdir, settings, caplog, language):
    """
    Ensure load_sfe_i18n_messages finds the right language file and returns its content as string.

    django.utils.translation.get_language() returns 'jp-jp' or 'fr-ca' instead of 'jp_JP' or 'fr_CA' respectively.

    This test checks load_sfe_i18n_messages on both formats.
    """
    caplog.set_level(logging.INFO)
    settings.REPO_ROOT = tmpdir
    studio_frontend_messages_dir = tmpdir / 'conf/plugins-locale/studio-frontend'
    os.makedirs(studio_frontend_messages_dir)
    messages_path = studio_frontend_messages_dir / 'jp_JP.json'
    messages_path.write_text('{"homepage": "Homepage"}', encoding='utf-8')
    assert studiofrontend.load_sfe_i18n_messages(language) == '{"homepage": "Homepage"}'
    assert caplog.text == ''
