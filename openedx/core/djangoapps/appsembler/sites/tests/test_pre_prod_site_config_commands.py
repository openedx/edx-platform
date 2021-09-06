"""
Tests for the pre-prod candidate site configurations export/import commands.
"""

import json

import pytest
from django.contrib.sites.models import Site

from django.core.management import call_command

from openedx.core.djangoapps.appsembler.sites import utils as sites_utils
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory


@pytest.fixture
def red_green_site_configs():
    green_config = SiteConfigurationFactory.create()
    green_config.site_values.update({
        'SITE_NAME': 'green.test.com',
        'LMS_ROOT_URL': 'https://green.test.com/',
        'custom_config': 'green',
    })
    green_config.save()
    red_config = SiteConfigurationFactory.create()
    red_config.site_values.update({
        'custom_config': 'red',
    })
    red_config.save()
    return {
        'green': green_config,
        'red': red_config,
    }


@pytest.mark.django_db
def test_site_configs_export(monkeypatch, tmpdir, red_green_site_configs):
    """
    Test the `./manage.py lms export_pre_prod_sites_config` command.
    """

    def mock_get_active_sites():
        return Site.objects.filter(configuration__isnull=False)

    monkeypatch.setattr(sites_utils, 'get_active_sites', mock_get_active_sites)
    export_file = tmpdir.join('sites.jsonl')

    call_command('export_pre_prod_sites_config', export_file.strpath)

    green_export_json = json.loads(export_file.readlines()[0])  # Green site is defined first.
    red_export_json = json.loads(export_file.readlines()[1])

    assert green_export_json['site_values']['custom_config'] == 'green'
    assert 'SITE_NAME' not in green_export_json['site_values']
    assert 'LMS_ROOT_URL' not in green_export_json['site_values']
    assert red_export_json['site_values']['custom_config'] == 'red'

    assert type(red_export_json['page_elements']) == dict, 'Check if page_elements is exported correctly'
    assert type(red_export_json['sass_variables']) == list, 'Check if sass_variables is exported correctly'


@pytest.mark.django_db
def test_site_configs_import(tmpdir, red_green_site_configs):
    """
    Test the `./manage.py lms export_pre_prod_sites_config` command.
    """
    export_file = tmpdir.join('sites.jsonl')
    # Write in the form of jsonlines.org
    with open(export_file.strpath, 'w', encoding='utf-8') as export_file_obj:
        export_file_obj.write(json.dumps({
            'site_id': red_green_site_configs['green'].site_id,
            'site_values': {
                'another_custom_value': 'slack.com',
            },
            'page_elements': {
                'dummy': 'dummy',
            },
            'sass_variables': [
                ['$brand-primary-color', ['rgba(0,1,1,1)', 'rgba(0,1,1,1)']],
            ],
        }))
        export_file_obj.write('\n')
        export_file_obj.write(json.dumps({
            'site_id': red_green_site_configs['red'].site_id,
            'site_values': {
                'yet_another_value': 'example.com',
            },
            'page_elements': {
                'dummyred': 'dummyred',
            },
            'sass_variables': [
                ['$brand-primary-color', ['rgba(0,2,2,2)', 'rgba(0,2,2,2)']],
            ],
        }))

    call_command('import_pre_prod_sites_config', export_file.strpath)

    green_config = red_green_site_configs['green']
    green_config.refresh_from_db()
    red_config = red_green_site_configs['red']
    red_config.refresh_from_db()

    assert green_config.get_value('custom_config') == 'green', 'existing values should be preserved'
    # assert green_config.get_value('another_custom_value') == 'slack.com'
    assert green_config.get_value('SITE_NAME'), 'URLs should not be deleted'
    assert green_config.get_value('LMS_ROOT_URL'), 'URLs should not be deleted'
    assert green_config.page_elements == {
        'dummy': 'dummy',
    }, 'Page elements should be overridden'
    assert green_config.sass_variables == [
        ['$brand-primary-color', ['rgba(0,1,1,1)', 'rgba(0,1,1,1)']]
    ], 'Sass variables should be overridden'

    assert red_config.get_value('yet_another_value') == 'example.com', 'Ensure site configs do not leak between sites'
