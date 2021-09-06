"""
Tests for the pre-prod candidate site configurations export/import commands.
"""

from django.core.management import call_command


def test_translate_command(capsys):
    """
    Test the `./manage.py lms tahoe_translate` command.
    """
    call_command(
        'tahoe_translate',
        'eo',
        'Sign in',
    )
    captured = capsys.readouterr()
    assert 'Sïgn' in captured.out, 'Dummy Esperanto language should be translated with weird accents'
