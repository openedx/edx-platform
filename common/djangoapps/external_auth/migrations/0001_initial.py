# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalAuthMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_id', models.CharField(max_length=255, db_index=True)),
                ('external_domain', models.CharField(max_length=255, db_index=True)),
                ('external_credentials', models.TextField(blank=True)),
                ('external_email', models.CharField(max_length=255, db_index=True)),
                ('external_name', models.CharField(db_index=True, max_length=255, blank=True)),
                ('internal_password', models.CharField(max_length=31, blank=True)),
                ('dtcreated', models.DateTimeField(auto_now_add=True, verbose_name=b'creation date')),
                ('dtsignup', models.DateTimeField(null=True, verbose_name=b'signup date')),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='externalauthmap',
            unique_together=set([('external_id', 'external_domain')]),
        ),
    ]
