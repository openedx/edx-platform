from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0010_auto_20170112_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persistentcoursegrade',
            name='course_edited_timestamp',
            field=models.DateTimeField(null=True, verbose_name='Last content edit timestamp', blank=True),
        ),
        migrations.AlterField(
            model_name='persistentsubsectiongrade',
            name='course_version',
            field=models.CharField(max_length=255, verbose_name='Guid of latest course version', blank=True),
        ),
        migrations.AlterField(
            model_name='persistentsubsectiongrade',
            name='subtree_edited_timestamp',
            field=models.DateTimeField(null=True, verbose_name='Last content edit timestamp', blank=True),
        ),
    ]
