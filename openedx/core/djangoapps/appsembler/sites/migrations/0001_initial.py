# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_auto_20170516_0517'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlternativeDomain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('domain', models.CharField(max_length=500)),
                ('site', models.OneToOneField(related_name='alternative_domain', to='sites.Site')),
            ],
        ),
    ]
