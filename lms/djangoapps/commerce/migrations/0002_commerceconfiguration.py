# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commerce', '0001_data__add_ecommerce_service_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommerceConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('checkout_on_ecommerce_service', models.BooleanField(default=False, help_text='Use the checkout page hosted by the E-Commerce service.')),
                ('single_course_checkout_page', models.CharField(default=b'/basket/single-item/', help_text='Path to single course checkout page hosted by the E-Commerce service.', max_length=255)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
    ]
