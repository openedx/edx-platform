# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EntitlementGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Name of the group', max_length=255)),
                ('kind', models.CharField(max_length=50, choices=[(b'enterprise_customer', 'Enterprise Customer')])),
            ],
        ),
        migrations.CreateModel(
            name='EntitlementModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(help_text='Entitlement type', max_length=255)),
                ('scope_id', models.CharField(help_text='ID of an object Entitlement is scoped to', max_length=4000)),
                ('parameters', jsonfield.fields.JSONField(default={}, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='entitlementgroup',
            name='entitlements',
            field=models.ManyToManyField(to='entitlements.EntitlementModel'),
        ),
        migrations.AddField(
            model_name='entitlementgroup',
            name='users',
            field=models.ManyToManyField(related_name='entitlement_groups', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
