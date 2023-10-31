"""  # lint-amnesty, pylint: disable=django-not-configured
Tests of the update_fixtures management command for bok-choy test database
initialization.
"""


import os

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command


@pytest.fixture(scope='function')
def sites(db):  # lint-amnesty, pylint: disable=unused-argument
    Site.objects.create(name='cms', domain='localhost:8031')
    Site.objects.create(name='lms', domain='localhost:8003')


def test_localhost(db, monkeypatch, sites):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    monkeypatch.delitem(os.environ, 'BOK_CHOY_HOSTNAME', raising=False)
    call_command('update_fixtures')
    assert Site.objects.get(name='cms').domain == 'localhost:8031'
    assert Site.objects.get(name='lms').domain == 'localhost:8003'


def test_devstack_cms(db, monkeypatch, sites):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    monkeypatch.setitem(os.environ, 'BOK_CHOY_HOSTNAME', 'edx.devstack.cms')
    monkeypatch.setitem(os.environ, 'BOK_CHOY_CMS_PORT', '18031')
    monkeypatch.setitem(os.environ, 'BOK_CHOY_LMS_PORT', '18003')
    call_command('update_fixtures')
    assert Site.objects.get(name='cms').domain == 'edx.devstack.cms:18031'
    assert Site.objects.get(name='lms').domain == 'edx.devstack.cms:18003'


def test_devstack_lms(db, monkeypatch, sites):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    monkeypatch.setitem(os.environ, 'BOK_CHOY_HOSTNAME', 'edx.devstack.lms')
    monkeypatch.setitem(os.environ, 'BOK_CHOY_CMS_PORT', '18031')
    monkeypatch.setitem(os.environ, 'BOK_CHOY_LMS_PORT', '18003')
    call_command('update_fixtures')
    assert Site.objects.get(name='cms').domain == 'edx.devstack.lms:18031'
    assert Site.objects.get(name='lms').domain == 'edx.devstack.lms:18003'
