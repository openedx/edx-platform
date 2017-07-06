# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppVersionConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('platform', models.CharField(max_length=50, choices=[(b'Android', b'Android'), (b'iOS', b'iOS')])),
                ('version', models.CharField(help_text=b'Version should be in the format X.X.X.Y where X is a number and Y is alphanumeric', max_length=50)),
                ('major_version', models.IntegerField()),
                ('minor_version', models.IntegerField()),
                ('patch_version', models.IntegerField()),
                ('expire_at', models.DateTimeField(null=True, verbose_name=b'Expiry date for platform version', blank=True)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-major_version', '-minor_version', '-patch_version'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='appversionconfig',
            unique_together=set([('platform', 'version')]),
        ),
    ]
