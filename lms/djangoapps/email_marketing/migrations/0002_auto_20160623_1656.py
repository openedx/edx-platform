# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_abandoned_cart_delay',
            field=models.IntegerField(default=60, help_text='Sailthru minutes to wait before sending abandoned cart message.'),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_abandoned_cart_template',
            field=models.CharField(help_text='Sailthru template to use on abandoned cart reminder. ', max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_content_cache_age',
            field=models.IntegerField(default=3600, help_text='Number of seconds to cache course content retrieved from Sailthru.'),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_enroll_cost',
            field=models.IntegerField(default=100, help_text='Cost in cents to report to Sailthru for enrolls.'),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_enroll_template',
            field=models.CharField(help_text='Sailthru send template to use on enrolling for audit. ', max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_get_tags_from_sailthru',
            field=models.BooleanField(default=True, help_text='Use the Sailthru content API to fetch course tags.'),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_purchase_template',
            field=models.CharField(help_text='Sailthru send template to use on purchasing a course seat. ', max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_upgrade_template',
            field=models.CharField(help_text='Sailthru send template to use on upgrading a course. ', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_activation_template',
            field=models.CharField(help_text='Sailthru template to use on activation send. ', max_length=20, blank=True),
        ),
    ]
