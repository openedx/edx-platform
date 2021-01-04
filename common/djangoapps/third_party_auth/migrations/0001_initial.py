# -*- coding: utf-8 -*-


import django.db.models.deletion
from openedx.core.lib.hash_utils import create_hash256
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LTIProviderConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('icon_class', models.CharField(default=u'fa-sign-in', help_text=u'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50)),
                ('name', models.CharField(help_text=u'Name of this provider (shown to users)', max_length=50)),
                ('secondary', models.BooleanField(default=False, help_text='Secondary providers are displayed less prominently, in a separate list of "Institution" login providers.')),
                ('skip_registration_form', models.BooleanField(default=False, help_text='If this option is enabled, users will not be asked to confirm their details (name, email, etc.) during the registration process. Only select this option for trusted providers that are known to provide accurate user information.')),
                ('skip_email_verification', models.BooleanField(default=False, help_text='If this option is selected, users will not be required to confirm their email, and their account will be activated immediately upon registration.')),
                ('lti_consumer_key', models.CharField(help_text=u'The name that the LTI Tool Consumer will use to identify itself', max_length=255)),
                ('lti_hostname', models.CharField(default=u'localhost', help_text=u'The domain that  will be acting as the LTI consumer.', max_length=255, db_index=True)),
                ('lti_consumer_secret', models.CharField(default=create_hash256, help_text=u'The shared secret that the LTI Tool Consumer will use to authenticate requests. Only this edX instance and this tool consumer instance should know this value. For increased security, you can avoid storing this in your database by leaving this field blank and setting SOCIAL_AUTH_LTI_CONSUMER_SECRETS = {"consumer key": "secret", ...} in your instance\'s Django setttigs (or lms.auth.json)', max_length=255, blank=True)),
                ('lti_max_timestamp_age', models.IntegerField(default=10, help_text=u'The maximum age of oauth_timestamp values, in seconds.')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Provider Configuration (LTI)',
                'verbose_name_plural': 'Provider Configuration (LTI)',
            },
        ),
        migrations.CreateModel(
            name='OAuth2ProviderConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('icon_class', models.CharField(default=u'fa-sign-in', help_text=u'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50)),
                ('name', models.CharField(help_text=u'Name of this provider (shown to users)', max_length=50)),
                ('secondary', models.BooleanField(default=False, help_text='Secondary providers are displayed less prominently, in a separate list of "Institution" login providers.')),
                ('skip_registration_form', models.BooleanField(default=False, help_text='If this option is enabled, users will not be asked to confirm their details (name, email, etc.) during the registration process. Only select this option for trusted providers that are known to provide accurate user information.')),
                ('skip_email_verification', models.BooleanField(default=False, help_text='If this option is selected, users will not be required to confirm their email, and their account will be activated immediately upon registration.')),
                ('backend_name', models.CharField(help_text=u'Which python-social-auth OAuth2 provider backend to use. The list of backend choices is determined by the THIRD_PARTY_AUTH_BACKENDS setting.', max_length=50, db_index=True)),
                ('key', models.TextField(verbose_name=u'Client ID', blank=True)),
                ('secret', models.TextField(help_text=u'For increased security, you can avoid storing this in your database by leaving  this field blank and setting SOCIAL_AUTH_OAUTH_SECRETS = {"(backend name)": "secret", ...} in your instance\'s Django settings (or lms.auth.json)', verbose_name=u'Client Secret', blank=True)),
                ('other_settings', models.TextField(help_text=u'Optional JSON object with advanced settings, if any.', blank=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Provider Configuration (OAuth)',
                'verbose_name_plural': 'Provider Configuration (OAuth)',
            },
        ),
        migrations.CreateModel(
            name='SAMLConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('private_key', models.TextField(help_text=u'To generate a key pair as two files, run "openssl req -new -x509 -days 3652 -nodes -out saml.crt -keyout saml.key". Paste the contents of saml.key here. For increased security, you can avoid storing this in your database by leaving this field blank and setting it via the SOCIAL_AUTH_SAML_SP_PRIVATE_KEY setting in your instance\'s Django settings (or lms.auth.json).', blank=True)),
                ('public_key', models.TextField(help_text=u"Public key certificate. For increased security, you can avoid storing this in your database by leaving this field blank and setting it via the SOCIAL_AUTH_SAML_SP_PUBLIC_CERT setting in your instance's Django settings (or lms.auth.json).", blank=True)),
                ('entity_id', models.CharField(default=u'http://saml.example.com', max_length=255, verbose_name=u'Entity ID')),
                ('org_info_str', models.TextField(default=u'{"en-US": {"url": "http://www.example.com", "displayname": "Example Inc.", "name": "example"}}', help_text=u"JSON dictionary of 'url', 'displayname', and 'name' for each language", verbose_name=u'Organization Info')),
                ('other_config_str', models.TextField(default=u'{\n"SECURITY_CONFIG": {"metadataCacheDuration": 604800, "signMetadata": false}\n}', help_text=u'JSON object defining advanced settings that are passed on to python-saml. Valid keys that can be set here include: SECURITY_CONFIG and SP_EXTRA')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'SAML Configuration',
                'verbose_name_plural': 'SAML Configuration',
            },
        ),
        migrations.CreateModel(
            name='SAMLProviderConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('icon_class', models.CharField(default=u'fa-sign-in', help_text=u'The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50)),
                ('name', models.CharField(help_text=u'Name of this provider (shown to users)', max_length=50)),
                ('secondary', models.BooleanField(default=False, help_text='Secondary providers are displayed less prominently, in a separate list of "Institution" login providers.')),
                ('skip_registration_form', models.BooleanField(default=False, help_text='If this option is enabled, users will not be asked to confirm their details (name, email, etc.) during the registration process. Only select this option for trusted providers that are known to provide accurate user information.')),
                ('skip_email_verification', models.BooleanField(default=False, help_text='If this option is selected, users will not be required to confirm their email, and their account will be activated immediately upon registration.')),
                ('backend_name', models.CharField(default=u'tpa-saml', help_text=u"Which python-social-auth provider backend to use. 'tpa-saml' is the standard edX SAML backend.", max_length=50)),
                ('idp_slug', models.SlugField(help_text=u'A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"', max_length=30)),
                ('entity_id', models.CharField(help_text=u'Example: https://idp.testshib.org/idp/shibboleth', max_length=255, verbose_name=u'Entity ID')),
                ('metadata_source', models.CharField(help_text=u"URL to this provider's XML metadata. Should be an HTTPS URL. Example: https://www.testshib.org/metadata/testshib-providers.xml", max_length=255)),
                ('attr_user_permanent_id', models.CharField(help_text=u'URN of the SAML attribute that we can use as a unique, persistent user ID. Leave blank for default.', max_length=128, verbose_name=u'User ID Attribute', blank=True)),
                ('attr_full_name', models.CharField(help_text=u"URN of SAML attribute containing the user's full name. Leave blank for default.", max_length=128, verbose_name=u'Full Name Attribute', blank=True)),
                ('attr_first_name', models.CharField(help_text=u"URN of SAML attribute containing the user's first name. Leave blank for default.", max_length=128, verbose_name=u'First Name Attribute', blank=True)),
                ('attr_last_name', models.CharField(help_text=u"URN of SAML attribute containing the user's last name. Leave blank for default.", max_length=128, verbose_name=u'Last Name Attribute', blank=True)),
                ('attr_username', models.CharField(help_text=u'URN of SAML attribute to use as a suggested username for this user. Leave blank for default.', max_length=128, verbose_name=u'Username Hint Attribute', blank=True)),
                ('attr_email', models.CharField(help_text=u"URN of SAML attribute containing the user's email address[es]. Leave blank for default.", max_length=128, verbose_name=u'Email Attribute', blank=True)),
                ('other_settings', models.TextField(help_text=u'For advanced use cases, enter a JSON object with addtional configuration. The tpa-saml backend supports only {"requiredEntitlements": ["urn:..."]} which can be used to require the presence of a specific eduPersonEntitlement.', verbose_name=u'Advanced settings', blank=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'Provider Configuration (SAML IdP)',
                'verbose_name_plural': 'Provider Configuration (SAML IdPs)',
            },
        ),
        migrations.CreateModel(
            name='SAMLProviderData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fetched_at', models.DateTimeField(db_index=True)),
                ('expires_at', models.DateTimeField(null=True, db_index=True)),
                ('entity_id', models.CharField(max_length=255, db_index=True)),
                ('sso_url', models.URLField(verbose_name=u'SSO URL')),
                ('public_key', models.TextField()),
            ],
            options={
                'ordering': ('-fetched_at',),
                'verbose_name': 'SAML Provider Data',
                'verbose_name_plural': 'SAML Provider Data',
            },
        ),
    ]
