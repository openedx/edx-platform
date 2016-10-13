# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('default', '0003_alter_email_max_length'),
        ('third_party_auth', '0005_add_site_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDataSharingConsentAudit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('state', models.CharField(default=b'not_set', help_text='Stores whether the user linked to the attached UserSocialAuth object has consented to have their information shared with the SSO provider linked to the attached UserSocialAuth object.', max_length=8, choices=[(b'not_set', b'Not set'), (b'enabled', b'Enabled'), (b'disabled', b'Disabled')])),
                ('user_social_auth', models.OneToOneField(related_name='data_sharing_consent_audit', to='default.UserSocialAuth', help_text='Links to a particular item in the UserSocialAuth table; each UserSocialAuth object uniquely links a particular user with a particular SSO provider.')),
            ],
            options={
                'verbose_name': 'Data Sharing Consent Audit State',
                'verbose_name_plural': 'Data Sharing Consent Audit States',
            },
        ),
        migrations.CreateModel(
            name='UserDataSharingConsentAuditHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('previous_state', models.CharField(default=b'not_set', help_text='The state of the linked UserDataSharingConsentAudit prior to the state transition indicated by this record.', max_length=8, choices=[(b'not_set', b'Not set'), (b'enabled', b'Enabled'), (b'disabled', b'Disabled')])),
                ('new_state', models.CharField(default=b'disabled', help_text='The state of the linked UserDataSharingConsentAudit after the state transition indicated by this record.', max_length=8, choices=[(b'not_set', b'Not set'), (b'enabled', b'Enabled'), (b'disabled', b'Disabled')])),
                ('current_state', models.ForeignKey(related_name='historical_changes', to='third_party_auth.UserDataSharingConsentAudit', help_text='The UserDataSharingConsentAudit object that encodes the state at present of whether this user has given consent for data sharing to take place.')),
            ],
            options={
                'verbose_name': 'Data Sharing Consent Historical Entry',
                'verbose_name_plural': 'Data Sharing Consent Historical Entries',
            },
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='data_sharing_consent',
            field=models.CharField(default=b'disabled', help_text='Whether this SSO requires data sharing permissions from users', max_length=8, choices=[(b'disabled', b'Disabled'), (b'optional', b'Optional'), (b'required', b'Required')]),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='data_sharing_consent',
            field=models.CharField(default=b'disabled', help_text='Whether this SSO requires data sharing permissions from users', max_length=8, choices=[(b'disabled', b'Disabled'), (b'optional', b'Optional'), (b'required', b'Required')]),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='data_sharing_consent',
            field=models.CharField(default=b'disabled', help_text='Whether this SSO requires data sharing permissions from users', max_length=8, choices=[(b'disabled', b'Disabled'), (b'optional', b'Optional'), (b'required', b'Required')]),
        ),
    ]
