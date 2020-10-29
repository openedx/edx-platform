# -*- coding: utf-8 -*-


import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(help_text='Name of this user attribute.', max_length=255)),
                ('value', models.CharField(help_text='Value of this user attribute.', max_length=255)),
                ('user', models.ForeignKey(related_name='attributes', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userattribute',
            unique_together=set([('user', 'name')]),
        ),
    ]
