# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0001_initial'),
        ('third_party_auth', '0002_schema__provider_icon_image'),
        ('third_party_auth', '0003_samlproviderconfig_debug_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='LTIProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=True
            ),
            preserve_default=False
        ),
        migrations.AlterField(
            model_name='LTIProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=False
            )
        ),
        migrations.AddField(
            model_name='OAuth2ProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=True
            ),
            preserve_default=False
        ),
        migrations.AlterField(
            model_name='OAuth2ProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=False
            )
        ),
        migrations.AddField(
            model_name='SAMLProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=True
            ),
            preserve_default=False
        ),
        migrations.AlterField(
            model_name='SAMLProviderConfig',
            name='visible',
            field=models.BooleanField(
                help_text=u'If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.',
                default=False
            )
        ),
    ]
