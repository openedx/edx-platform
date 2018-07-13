# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_dispatch', '0006_drop_application_id_constraints'),
    ]

    database_operations = [
        migrations.AlterField(
            model_name='RestrictedApplication',
            name='application',
            field=models.ForeignKey(
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL, on_delete=models.CASCADE
            )
        ),

        migrations.AlterField(
            model_name='ScopedApplicationOrganization',
            name='application',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name='organizations',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

        migrations.AlterField(
            model_name='ApplicationOrganization',
            name='application',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name='organizations',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

        migrations.AlterField(
            model_name='ApplicationAccess',
            name='application',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name='access',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

    ]
