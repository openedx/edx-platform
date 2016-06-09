# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('xblock_django', '0002_auto_20160204_0809'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalXBlockConfig',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('change_date', models.DateTimeField(verbose_name='change date', editable=False, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('template', models.CharField(default=b'', max_length=255, blank=True)),
                ('support_level', models.CharField(default=b'ud', max_length=2, choices=[(b'fs', 'Fully Supported'), (b'ps', 'Provisionally Supported'), (b'ua', 'Unsupported (Opt-in allowed)'), (b'ud', 'Unsupported (Opt-in disallowed)'), (b'da', 'Disabled')])),
                ('deprecated', models.BooleanField(default=False, help_text="Only XBlocks listed in a course's Advanced Module List can be flagged as deprecated. Note that deprecation is by XBlock name, and is not specific to template.", verbose_name='show deprecation messaging in Studio')),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('changed_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical x block config',
            },
        ),
        migrations.CreateModel(
            name='XBlockConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now=True, verbose_name='change date')),
                ('name', models.CharField(max_length=255)),
                ('template', models.CharField(default=b'', max_length=255, blank=True)),
                ('support_level', models.CharField(default=b'ud', max_length=2, choices=[(b'fs', 'Fully Supported'), (b'ps', 'Provisionally Supported'), (b'ua', 'Unsupported (Opt-in allowed)'), (b'ud', 'Unsupported (Opt-in disallowed)'), (b'da', 'Disabled')])),
                ('deprecated', models.BooleanField(default=False, help_text="Only XBlocks listed in a course's Advanced Module List can be flagged as deprecated. Note that deprecation is by XBlock name, and is not specific to template.", verbose_name='show deprecation messaging in Studio')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='changed by')),
            ],
        ),
        migrations.CreateModel(
            name='XBlockConfigFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='xblockconfig',
            unique_together=set([('name', 'template')]),
        ),
    ]
