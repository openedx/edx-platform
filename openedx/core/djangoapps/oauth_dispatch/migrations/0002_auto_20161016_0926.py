# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_dispatch', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='restrictedapplication',
            name='_allowed_scopes',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='restrictedapplication',
            name='_org_associations',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='restrictedapplication',
            name='application',
            field=models.ForeignKey(related_name='restricted_application', to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ),
    ]
