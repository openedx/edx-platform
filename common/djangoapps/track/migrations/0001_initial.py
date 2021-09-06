# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TrackingLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dtcreated', models.DateTimeField(auto_now_add=True, verbose_name=u'creation date')),
                ('username', models.CharField(max_length=32, blank=True)),
                ('ip', models.CharField(max_length=32, blank=True)),
                ('event_source', models.CharField(max_length=32)),
                ('event_type', models.CharField(max_length=512, blank=True)),
                ('event', models.TextField(blank=True)),
                ('agent', models.CharField(max_length=256, blank=True)),
                ('page', models.CharField(max_length=512, null=True, blank=True)),
                ('time', models.DateTimeField(verbose_name=u'event time')),
                ('host', models.CharField(max_length=64, blank=True)),
            ],
            options={
                'db_table': 'track_trackinglog',
            },
        ),
    ]
