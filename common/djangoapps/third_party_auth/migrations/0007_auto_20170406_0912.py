# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0006_samlproviderconfig_automatic_refresh_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlproviderconfig',
            name='identity_provider_type',
            field=models.CharField(default=b'standard_saml_provider', help_text=b'Some SAML providers require special behavior. For example, SAP SuccessFactors SAML providers require an additional API call to retrieve user metadata not provided in the SAML response. Select the provider type which best matches your use case. If in doubt, choose the Standard SAML Provider type.', max_length=128, verbose_name=b'Identity Provider Type', choices=[(b'standard_saml_provider', b'Standard SAML provider'), (b'sap_success_factors', b'SAP SuccessFactors provider')]),
        ),
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='other_settings',
            field=models.TextField(help_text=b'For advanced use cases, enter a JSON object with addtional configuration. The tpa-saml backend supports only {"requiredEntitlements": ["urn:..."]} which can be used to require the presence of a specific eduPersonEntitlement. Custom provider types, as selected in the "Identity Provider Type" field, may make use of the information stored in this field for configuration.', verbose_name=b'Advanced settings', blank=True),
        ),
    ]
