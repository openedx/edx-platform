# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_dispatch', '0005_applicationaccess_type'),
    ]

    database_operations = [
        # Created in 0001_initial.py
        migrations.AlterField(
            model_name='RestrictedApplication',
            name='application',
            field=models.ForeignKey(
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL, db_constraint=False, on_delete=models.CASCADE
            )
        ),

        # Created in 0002_scopedapplication_scopedapplicationorganization.py
        migrations.AlterField(
            model_name='ScopedApplicationOrganization',
            name='application',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, db_constraint=False, related_name='organizations',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

        # Created in 0004_auto_20180626_1349.py
        migrations.AlterField(
            model_name='ApplicationOrganization',
            name='application',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, db_constraint=False, related_name='organizations',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

        # Altered in 0005_applicationaccess_type.py
        migrations.AlterField(
            model_name='ApplicationAccess',
            name='application',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, db_constraint=False, related_name='access',
                to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL
            )
        ),

    ]
