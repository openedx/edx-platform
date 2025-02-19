"""
Tests for the modulestore.django module
"""

from pathlib import Path
from unittest.mock import patch

import django.utils.translation

from xmodule.modulestore.django import XBlockI18nService


def test_get_python_locale_with_atlas_oep58_translations(mock_modern_xblock):
    """
    Test that the XBlockI18nService.get_python_locale() method finds the atlas locale if it exists.

    More on OEP-58 and atlas pull: https://docs.openedx.org/en/latest/developers/concepts/oep58.html.
    """
    i18n_service = XBlockI18nService()
    block = mock_modern_xblock['modern_xblock']
    domain, locale_path = i18n_service.get_python_locale(block)

    assert locale_path.endswith('conf/plugins-locale/xblock.v1/my_modern_xblock'), 'Uses atlas locale if found.'
    assert domain == 'django', 'Uses django domain when atlas locale is found.'


@patch('importlib.resources.files', return_value=Path('/lib/my_legacy_xblock'))
def test_get_python_locale_with_bundled_translations(mock_modern_xblock):
    """
    Ensure that get_python_locale() falls back to XBlock internal translations if atlas translations weren't pulled.

    Pre-OEP-58 translations were stored in the `translations` directory of the XBlock which is
    accessible via the `importlib.resources.files` function.
    """
    i18n_service = XBlockI18nService()
    block = mock_modern_xblock['legacy_xblock']
    domain, path = i18n_service.get_python_locale(block)

    assert path == '/lib/my_legacy_xblock/translations', 'Backward compatible with pre-OEP-58.'
    assert domain == 'text', 'Use the legacy `text` domain for backward compatibility with old XBlocks.'


def test_i18n_service_translator_with_modern_xblock(mock_modern_xblock):
    """
    Ensure the XBlockI18nService uses the atlas translations if found.
    """
    block = mock_modern_xblock['modern_xblock']

    with django.utils.translation.override('fr'):
        i18n_service = XBlockI18nService(block)
        assert i18n_service.translator is django.utils.translation, 'French is not pulled by `mock_modern_xblock`.'

    with django.utils.translation.override('tr'):
        i18n_service = XBlockI18nService(block)
        assert i18n_service.translator is not django.utils.translation, 'Turkish is pulled by `mock_modern_xblock`.'
