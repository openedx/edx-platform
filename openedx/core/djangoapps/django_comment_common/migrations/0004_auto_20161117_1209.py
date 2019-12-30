# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_comment_common', '0003_enable_forums'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumsconfig',
            name='connection_timeout',
            field=models.FloatField(default=5.0, help_text=u'Seconds to wait when trying to connect to the comment service.'),
        ),
    ]
