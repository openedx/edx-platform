# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollment',
            name='mode',
            field=models.CharField(default=u'audit', max_length=100),
        ),
        migrations.AlterField(
            model_name='historicalcourseenrollment',
            name='mode',
            field=models.CharField(default=u'audit', max_length=100),
        ),
    ]
