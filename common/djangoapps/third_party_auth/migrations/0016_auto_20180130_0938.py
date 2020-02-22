# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0015_samlproviderconfig_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlconfiguration',
            name='slug',
            field=models.SlugField(default=u'default', help_text=u'A short string uniquely identifying this configuration. Cannot contain spaces. Examples: "ubc", "mit-staging"', max_length=30),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='saml_configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='third_party_auth.SAMLConfiguration', null=True),
        ),
    ]
