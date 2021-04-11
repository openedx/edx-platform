# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customcourseforedx',
            name='structure_json',
            field=models.TextField(null=True, verbose_name=u'Structure JSON', blank=True),
        ),
    ]
