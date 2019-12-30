# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0007_certificateinvalidation'),
        ('badges', '0002_data__migrate_assertions'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='badgeassertion',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='badgeassertion',
            name='user',
        ),
        migrations.DeleteModel(
            name='BadgeImageConfiguration',
        ),
        migrations.DeleteModel(
            name='BadgeAssertion',
        ),
    ]
