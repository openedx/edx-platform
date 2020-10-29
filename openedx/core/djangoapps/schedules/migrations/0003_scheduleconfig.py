# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedules', '0002_auto_20170816_1532'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('create_schedules', models.BooleanField(default=False)),
                ('enqueue_recurring_nudge', models.BooleanField(default=False)),
                ('deliver_recurring_nudge', models.BooleanField(default=False)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
                ('site', models.ForeignKey(to='sites.Site', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
    ]
