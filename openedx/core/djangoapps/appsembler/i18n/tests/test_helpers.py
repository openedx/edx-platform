"""
Test the i18n module helpers.
"""
from openedx.core.djangoapps.appsembler.i18n.helpers import xblock_translate


def test_xblock_translate():
    translated_text = xblock_translate('drag-and-drop-v2', 'eo', 'The Top Zone')
    assert 'Töp' in translated_text
