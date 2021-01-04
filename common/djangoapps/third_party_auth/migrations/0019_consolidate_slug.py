# -*- coding: utf-8 -*-
"""
Custom migration script to add slug field to all ProviderConfig models.
"""


from django.db import migrations, models
from django.utils.text import slugify


def fill_slug_field(apps, schema_editor):
    """
    Fill in the slug field for each ProviderConfig class for backwards compatability.
    """
    OAuth2ProviderConfig = apps.get_model('third_party_auth', 'OAuth2ProviderConfig')
    SAMLProviderConfig = apps.get_model('third_party_auth', 'SAMLProviderConfig')
    LTIProviderConfig = apps.get_model('third_party_auth', 'LTIProviderConfig')

    for config in OAuth2ProviderConfig.objects.all():
        config.slug = config.provider_slug
        config.save()

    for config in SAMLProviderConfig.objects.all():
        config.slug = config.idp_slug
        config.save()

    for config in LTIProviderConfig.objects.all():
        config.slug = slugify(config.lti_consumer_key)
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0018_auto_20180327_1631'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='slug',
            field=models.SlugField(default=u'default', help_text=u'A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"', max_length=30),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='slug',
            field=models.SlugField(default=u'default', help_text=u'A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"', max_length=30),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='slug',
            field=models.SlugField(default=u'default', help_text=u'A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"', max_length=30),
        ),
        migrations.RunPython(fill_slug_field, reverse_code=migrations.RunPython.noop),
    ]
