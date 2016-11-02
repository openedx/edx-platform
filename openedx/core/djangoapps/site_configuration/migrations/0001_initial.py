# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('values', jsonfield.fields.JSONField(blank=True)),
                ('site', models.OneToOneField(related_name='configuration', to='sites.Site')),
            ],
        ),
        migrations.CreateModel(
            name='SiteConfigurationHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('values', jsonfield.fields.JSONField(blank=True)),
                ('site', models.ForeignKey(related_name='configuration_histories', to='sites.Site')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),
    ]
