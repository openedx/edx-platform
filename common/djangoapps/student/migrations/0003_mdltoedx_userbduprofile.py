# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='MdlToEdx',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link', models.CharField(max_length=255, blank=True)),
                ('sent', models.BooleanField(default=False)),
                ('visited', models.BooleanField(default=False)),
                ('timesent', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('mdl_user_id', models.IntegerField(unique=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'edx_mdl',
            },
        ),
        migrations.CreateModel(
            name='UserBDUProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ambassador', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'auth_userbduprofile',
            },
        ),
    ]
