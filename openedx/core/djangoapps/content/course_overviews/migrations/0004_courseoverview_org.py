# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0003_courseoverviewgeneratedhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='org',
            field=models.TextField(default=u'outdated_entry', max_length=255),
        ),
    ]
