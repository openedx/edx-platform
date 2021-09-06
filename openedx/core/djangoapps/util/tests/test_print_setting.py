# -*- coding: utf-8 -*-


import pytest
from django.core.management import CommandError, call_command


def test_without_args(capsys):
    with pytest.raises(CommandError, match='Error: the following arguments are required: setting'):
        call_command('print_setting')


def test_with_setting_args(capsys):
    call_command('print_setting', 'DEBUG')

    out, err = capsys.readouterr()
    assert 'False' in out
    assert 'INSTALLED_APPS' not in out
