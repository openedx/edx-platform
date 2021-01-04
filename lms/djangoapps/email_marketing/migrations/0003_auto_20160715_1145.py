# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0002_auto_20160623_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_lms_url_override',
            field=models.CharField(help_text='Optional lms url scheme + host used to construct urls for content library, e.g. https://courses.edx.org.', max_length=80, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_abandoned_cart_delay',
            field=models.IntegerField(default=60, help_text='Sailthru minutes to wait before sending abandoned cart message. Deprecated.'),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_abandoned_cart_template',
            field=models.CharField(help_text='Sailthru template to use on abandoned cart reminder. Deprecated.', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_purchase_template',
            field=models.CharField(help_text='Sailthru send template to use on purchasing a course seat. Deprecated ', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_upgrade_template',
            field=models.CharField(help_text='Sailthru send template to use on upgrading a course. Deprecated ', max_length=20, blank=True),
        ),
    ]
