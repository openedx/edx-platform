# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0015_samlproviderconfig_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlconfiguration',
            name='slug',
            field=models.SlugField(default=b'default', help_text=b'A short string uniquely identifying this configuration. Cannot contain spaces. Examples: "ubc", "mit-staging"', max_length=30),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='saml_configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='third_party_auth.SAMLConfiguration', null=True),
        ),
    ]
