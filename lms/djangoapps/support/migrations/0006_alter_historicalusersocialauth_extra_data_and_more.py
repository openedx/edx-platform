# Generated by Django 4.2.13 on 2024-06-27 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0005_unique_course_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalusersocialauth',
            name='extra_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='historicalusersocialauth',
            name='id',
            field=models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID'),
        ),
    ]
