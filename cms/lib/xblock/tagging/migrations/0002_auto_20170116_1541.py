# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tagavailablevalues',
            options={'ordering': ('id',), 'verbose_name': 'available tag value'},
        ),
        migrations.AlterModelOptions(
            name='tagcategories',
            options={'ordering': ('title',), 'verbose_name': 'tag category', 'verbose_name_plural': 'tag categories'},
        ),
    ]
