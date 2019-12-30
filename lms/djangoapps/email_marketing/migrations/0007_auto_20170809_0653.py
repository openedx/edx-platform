# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_marketing', '0006_auto_20170711_0615'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmarketingconfiguration',
            name='sailthru_welcome_template',
            field=models.CharField(help_text='Sailthru template to use on welcome send.', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='sailthru_activation_template',
            field=models.CharField(help_text='DEPRECATED: use sailthru_welcome_template instead.', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='emailmarketingconfiguration',
            name='welcome_email_send_delay',
            field=models.IntegerField(default=600, help_text='Number of seconds to delay the sending of User Welcome email after user has been created'),
        ),
    ]
