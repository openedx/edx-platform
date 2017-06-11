# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import migrations, models


attrs = (
    "attr_user_permanent_id",
    "attr_first_name",
    "attr_last_name",
    "attr_full_name",
    "attr_username",
    "attr_email"
)


def populate_urns_into_json(apps, schema_editor):
    SAMLProviderConfig = apps.get_model('third_party_auth', 'samlproviderconfig')
    for saml_provider_config in SAMLProviderConfig.objects.all():
        saml_provider_config.attributes = json.dumps({
            field: getattr(saml_provider_config, field) for field in attrs
        }, indent=4)
        saml_provider_config.save()


def populate_urns_from_json(apps, schema_editor):
    SAMLProviderConfig = apps.get_model('third_party_auth', 'samlproviderconfig')
    for saml_provider_config in SAMLProviderConfig.objects.all():
        attributes = json.loads(saml_provider_config.attributes)
        for field in attrs:
            setattr(saml_provider_config, field, attributes[field])
        saml_provider_config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0010_add_skip_hinted_login_dialog_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderconfig',
            name='attributes',
            field=models.TextField(default=b'{\n    "attr_last_name": "", \n    "attr_username": "", \n    "attr_user_permanent_id": "", \n    "attr_full_name": "", \n    "attr_email": "", \n    "attr_first_name": ""\n}', help_text=b"JSON of URNs of SAML attributes containing user data. Leave a value blank to use it's default.", verbose_name=b'Attributes Assertions'),
        ),
        migrations.RunPython(populate_urns_into_json, populate_urns_from_json),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_email',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_first_name',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_full_name',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_last_name',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_user_permanent_id',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='attr_username',
        ),
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='other_settings',
            field=models.TextField(help_text=b'For advanced use cases, enter a JSON object with additional configuration. The tpa-saml backend supports only {"requiredEntitlements": ["urn:..."]} which can be used to require the presence of a specific eduPersonEntitlement. Custom provider types, as selected in the "Identity Provider Type" field, may make use of the information stored in this field for configuration.', verbose_name=b'Advanced settings', blank=True),
        ),
    ]
