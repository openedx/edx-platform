# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0006_logoutviewconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationCookieConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('utm_cookie_name', models.CharField(help_text='Name of the UTM cookie', max_length=255)),
                ('affiliate_cookie_name', models.CharField(help_text='Name of the affiliate cookie', max_length=255)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
    ]
