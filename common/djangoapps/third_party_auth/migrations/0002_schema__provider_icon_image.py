# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import provider.utils


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTIProviderConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('icon_class', models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50)),
                ('name', models.CharField(help_text=b'Name of this provider (shown to users)', max_length=50)),
                ('secondary', models.BooleanField(default=False, help_text='Secondary providers are displayed less prominently, in a separate list of "Institution" login providers.')),
                ('skip_registration_form', models.BooleanField(default=False, help_text='If this option is enabled, users will not be asked to confirm their details (name, email, etc.) during the registration process. Only select this option for trusted providers that are known to provide accurate user information.')),
                ('skip_email_verification', models.BooleanField(default=False, help_text='If this option is selected, users will not be required to confirm their email, and their account will be activated immediately upon registration.')),
                ('lti_consumer_key', models.CharField(help_text=b'The name that the LTI Tool Consumer will use to identify itself', max_length=255)),
                ('lti_hostname', models.CharField(default=b'localhost', help_text=b'The domain that  will be acting as the LTI consumer.', max_length=255, db_index=True)),
                ('lti_consumer_secret', models.CharField(default=provider.utils.long_token, help_text=b'The shared secret that the LTI Tool Consumer will use to authenticate requests. Only this edX instance and this tool consumer instance should know this value. For increased security, you can avoid storing this in your database by leaving this field blank and setting SOCIAL_AUTH_LTI_CONSUMER_SECRETS = {"consumer key": "secret", ...} in your instance\'s Django setttigs (or lms.auth.json)', max_length=255, blank=True)),
                ('lti_max_timestamp_age', models.IntegerField(default=10, help_text=b'The maximum age of oauth_timestamp values, in seconds.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Provider Configuration (LTI)',
                'verbose_name_plural': 'Provider Configuration (LTI)',
            },
        ),
        migrations.CreateModel(
            name='ProviderApiPermissions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider_id', models.CharField(help_text=b'Uniquely identify a provider. This is different from backend_name.', max_length=255)),
                ('client', models.ForeignKey(to='oauth2.Client')),
            ],
            options={
                'verbose_name': 'Provider API Permission',
                'verbose_name_plural': 'Provider API Permissions',
            },
        ),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='icon_image',
            field=models.FileField(help_text=b'If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='ltiproviderconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='oauth2providerconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='samlproviderconfig',
            name='icon_class',
            field=models.CharField(default=b'fa-sign-in', help_text=b'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50, blank=True),
        ),
    ]
