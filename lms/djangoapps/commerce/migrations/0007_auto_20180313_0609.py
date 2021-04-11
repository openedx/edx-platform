# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0006_auto_20170424_1734'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commerceconfiguration',
            name='single_course_checkout_page',
        ),
        migrations.AddField(
            model_name='commerceconfiguration',
            name='basket_checkout_page',
            field=models.CharField(default=u'/basket/add/', help_text='Path to course(s) checkout page hosted by the E-Commerce service.', max_length=255),
        ),
    ]
