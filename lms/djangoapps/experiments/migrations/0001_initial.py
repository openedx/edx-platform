# -*- coding: utf-8 -*-



from django.db import migrations, models
from django.conf import settings
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('experiment_id', models.PositiveSmallIntegerField(verbose_name=u'Experiment ID', db_index=True)),
                ('key', models.CharField(max_length=255)),
                ('value', models.TextField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Experiment Data',
                'verbose_name_plural': 'Experiment Data',
            },
        ),
        migrations.AlterUniqueTogether(
            name='experimentdata',
            unique_together=set([('user', 'experiment_id', 'key')]),
        ),
        migrations.AlterIndexTogether(
            name='experimentdata',
            index_together=set([('user', 'experiment_id')]),
        ),
    ]
