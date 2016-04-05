# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api_admin', '0002_auto_20160325_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiAccessConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='apiaccessrequest',
            name='company_address',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='apiaccessrequest',
            name='company_name',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='company_address',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='company_name',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AlterField(
            model_name='apiaccessrequest',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
    ]
