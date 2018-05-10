# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0010_add_skip_hinted_login_dialog_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='other_settings',
            field=models.TextField(help_text=b'For advanced use cases, enter a JSON object with addtional configuration. The tpa-saml backend supports {"requiredEntitlements": ["urn:..."]}, which can be used to require the presence of a specific eduPersonEntitlement, and {"extra_field_definitions": [{"name": "...", "urn": "..."},...]}, which can be used to define registration form fields and the URNs that can be used to retrieve the relevant values from the SAML response. Custom provider types, as selected in the "Identity Provider Type" field, may make use of the information stored in this field for additional configuration.', verbose_name=b'Advanced settings', blank=True),
        ),
    ]
