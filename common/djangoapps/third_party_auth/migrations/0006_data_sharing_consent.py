# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default', '0003_alter_email_max_length'),
        ('third_party_auth', '0005_add_site_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSharingConsentSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False, help_text='If selected, this means that the user has chosen to share data with this SSO provider.')),
                ('date_set', models.DateTimeField(help_text='This field indicates the timestamp at which the object was created.', auto_now=True)),
                ('auth', models.OneToOneField(related_name='consent_setting', to='default.UserSocialAuth', help_text='The UserSocialAuth database row to which this consent is attached.')),
            ],
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='data_sharing_consent_error',
            field=models.CharField(help_text='If the SSO requires data sharing consent, but the user does not provide it at registration, text from this field will be used to inform the user of the error.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='data_sharing_consent_prompt',
            field=models.CharField(help_text='When data sharing consent is requested, this text will appear next to the relevant form element to help users make an informed decision about whether to grant consent.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='request_data_sharing_consent',
            field=models.BooleanField(default=True, help_text='If this option is selected, users will be presented with an option to share course information with the SSO provider when registering.'),
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='require_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='If this option is selected, users who sign in using this SSO provider will not be able to proceed unless they affirmatively select the option to grant data sharing consent.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='data_sharing_consent_error',
            field=models.CharField(help_text='If the SSO requires data sharing consent, but the user does not provide it at registration, text from this field will be used to inform the user of the error.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='data_sharing_consent_prompt',
            field=models.CharField(help_text='When data sharing consent is requested, this text will appear next to the relevant form element to help users make an informed decision about whether to grant consent.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='request_data_sharing_consent',
            field=models.BooleanField(default=True, help_text='If this option is selected, users will be presented with an option to share course information with the SSO provider when registering.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='require_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='If this option is selected, users who sign in using this SSO provider will not be able to proceed unless they affirmatively select the option to grant data sharing consent.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='data_sharing_consent_error',
            field=models.CharField(help_text='If the SSO requires data sharing consent, but the user does not provide it at registration, text from this field will be used to inform the user of the error.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='data_sharing_consent_prompt',
            field=models.CharField(help_text='When data sharing consent is requested, this text will appear next to the relevant form element to help users make an informed decision about whether to grant consent.', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='request_data_sharing_consent',
            field=models.BooleanField(default=True, help_text='If this option is selected, users will be presented with an option to share course information with the SSO provider when registering.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='require_data_sharing_consent',
            field=models.BooleanField(default=False, help_text='If this option is selected, users who sign in using this SSO provider will not be able to proceed unless they affirmatively select the option to grant data sharing consent.'),
        ),
    ]