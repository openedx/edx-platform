# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_auto_20170616_0618'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogintegration',
            name='long_term_cache_ttl',
            field=models.PositiveIntegerField(default=86400, help_text='Specified in seconds (defaults to 86400s, 24hr). In some cases the cache does needs to be refreshed less frequently. Enable long term caching of API responses by setting this to a value greater than 0.', verbose_name='Long Term Cache Time To Live'),
        ),
    ]
