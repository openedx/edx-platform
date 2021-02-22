# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_auto_20160531_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userattribute',
            name='name',
            field=models.CharField(help_text='Name of this user attribute.', max_length=255, db_index=True),
        ),
    ]
