# -*- coding: utf-8 -*-



from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coursetalk', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursetalkwidgetconfiguration',
            name='platform_key',
            field=models.CharField(help_text='The platform key associates CourseTalk widgets with your platform. Generally, it is the domain name for your platform. For example, if your platform is http://edx.org, the platform key is "edx".', max_length=50),
        ),
    ]
