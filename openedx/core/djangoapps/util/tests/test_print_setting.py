# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.core.management import call_command, CommandError


def test_without_args(capsys):
    with pytest.raises(CommandError, message='Error: too few arguments'):
        call_command('print_setting')


def test_with_setting_args(capsys):
    call_command('print_setting', 'DEBUG')

    out, err = capsys.readouterr()
    assert 'False' in out
    assert 'INSTALLED_APPS' not in out
