# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0008_auto_20170413_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='max_session_length',
            field=models.PositiveIntegerField(default=None, help_text='If this option is set, then users logging in using this SSO provider will have their session length limited to no longer than this value. If set to 0 (zero), the session will expire upon the user closing their browser. If left blank, the Django platform session default length will be used.', null=True, verbose_name=u'Max session length (seconds)', blank=True),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='max_session_length',
            field=models.PositiveIntegerField(default=None, help_text='If this option is set, then users logging in using this SSO provider will have their session length limited to no longer than this value. If set to 0 (zero), the session will expire upon the user closing their browser. If left blank, the Django platform session default length will be used.', null=True, verbose_name=u'Max session length (seconds)', blank=True),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='max_session_length',
            field=models.PositiveIntegerField(default=None, help_text='If this option is set, then users logging in using this SSO provider will have their session length limited to no longer than this value. If set to 0 (zero), the session will expire upon the user closing their browser. If left blank, the Django platform session default length will be used.', null=True, verbose_name=u'Max session length (seconds)', blank=True),
        ),
    ]
