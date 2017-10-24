# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('waffle_utils', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaffleFlagOrgOverrideModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('waffle_flag', models.CharField(max_length=255, db_index=True)),
                ('org_id', models.CharField(max_length=255, db_index=True)),
                ('override_choice', models.CharField(default=b'on', max_length=3, choices=[(b'on', 'Force On'), (b'off', 'Force Off')])),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Waffle flag org override',
                'verbose_name_plural': 'Waffle flag org overrides',
            },
        ),
    ]
