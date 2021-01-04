# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models


def fill_oauth2_slug(apps, schema_editor):
    """
    Fill in the provider_slug to be the same as backend_name for backwards compatability.
    """
    OAuth2ProviderConfig = apps.get_model('third_party_auth', 'OAuth2ProviderConfig')
    for config in OAuth2ProviderConfig.objects.all():
        config.provider_slug = config.backend_name
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('third_party_auth', '0004_add_visible_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='provider_slug',
            field=models.SlugField(
                default='temp',
                help_text=u'A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"',
                max_length=30
            ),
            preserve_default=False,
        ),
        migrations.RunPython(fill_oauth2_slug, reverse_code=migrations.RunPython.noop),
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='site',
            field=models.ForeignKey(
                related_name='ltiproviderconfigs',
                default=settings.SITE_ID,
                to='sites.Site',
                help_text='The Site that this provider configuration belongs to.',
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='site',
            field=models.ForeignKey(
                related_name='oauth2providerconfigs',
                default=settings.SITE_ID,
                to='sites.Site',
                help_text='The Site that this provider configuration belongs to.',
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='site',
            field=models.ForeignKey(
                related_name='samlproviderconfigs',
                default=settings.SITE_ID,
                to='sites.Site',
                help_text='The Site that this provider configuration belongs to.',
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name='samlconfiguration',
            name='site',
            field=models.ForeignKey(
                related_name='samlconfigurations',
                default=settings.SITE_ID,
                to='sites.Site',
                help_text='The Site that this SAML configuration belongs to.',
                on_delete=models.CASCADE,
            ),
        ),
    ]
