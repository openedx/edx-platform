# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SQLNotificationCallbackTimer',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('callback_at', models.DateTimeField(db_index=True)),
                ('class_name', models.CharField(max_length=255)),
                ('context', models.TextField(null=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('periodicity_min', models.IntegerField(null=True)),
                ('executed_at', models.DateTimeField(null=True)),
                ('err_msg', models.TextField(null=True)),
                ('results', models.TextField(null=True)),
            ],
            options={
                'db_table': 'edx_notifications_notificationcallbacktimer',
            },
        ),
        migrations.CreateModel(
            name='SQLNotificationChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'edx_notifications_notificationchannel',
            },
        ),
        migrations.CreateModel(
            name='SQLNotificationMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('namespace', models.CharField(max_length=128, null=True, db_index=True)),
                ('from_user_id', models.IntegerField(null=True)),
                ('payload', models.TextField()),
                ('deliver_no_earlier_than', models.DateTimeField(null=True)),
                ('expires_at', models.DateTimeField(null=True, db_index=True)),
                ('expires_secs_after_read', models.IntegerField(null=True)),
                ('priority', models.IntegerField(default=0)),
                ('resolve_links', models.TextField(null=True)),
                ('object_id', models.CharField(max_length=255, null=True, db_index=True)),
            ],
            options={
                'ordering': ['-created'],
                'db_table': 'edx_notifications_notificationmessage',
            },
        ),
        migrations.CreateModel(
            name='SQLNotificationPreference',
            fields=[
                ('name', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('display_name', models.CharField(max_length=255)),
                ('display_description', models.CharField(max_length=1023)),
                ('default_value', models.CharField(max_length=255, null=True)),
            ],
            options={
                'db_table': 'edx_notifications_notificationpreference',
            },
        ),
        migrations.CreateModel(
            name='SQLNotificationType',
            fields=[
                ('name', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('renderer', models.CharField(max_length=255)),
                ('renderer_context', models.TextField(null=True)),
            ],
            options={
                'db_table': 'edx_notifications_notificationtype',
            },
        ),
        migrations.CreateModel(
            name='SQLUserNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('user_id', models.IntegerField(db_index=True)),
                ('read_at', models.DateTimeField(null=True, db_index=True)),
                ('user_context', models.TextField(null=True)),
                ('msg', models.ForeignKey(to='edx_notifications.SQLNotificationMessage')),
            ],
            options={
                'ordering': ['-created'],
                'db_table': 'edx_notifications_usernotification',
            },
        ),
        migrations.CreateModel(
            name='SQLUserNotificationArchive',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('user_id', models.IntegerField(db_index=True)),
                ('read_at', models.DateTimeField(null=True, db_index=True)),
                ('user_context', models.TextField(null=True)),
                ('msg', models.ForeignKey(to='edx_notifications.SQLNotificationMessage')),
            ],
            options={
                'ordering': ['-created'],
                'db_table': 'edx_notifications_usernotificationarchive',
            },
        ),
        migrations.CreateModel(
            name='SQLUserNotificationPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('user_id', models.IntegerField(db_index=True)),
                ('value', models.CharField(max_length=255)),
                ('preference', models.ForeignKey(to='edx_notifications.SQLNotificationPreference')),
            ],
            options={
                'db_table': 'edx_notifications_usernotificationpreferences',
            },
        ),
        migrations.AddField(
            model_name='sqlnotificationmessage',
            name='msg_type',
            field=models.ForeignKey(to='edx_notifications.SQLNotificationType'),
        ),
        migrations.AlterUniqueTogether(
            name='sqlusernotificationarchive',
            unique_together=set([('user_id', 'msg')]),
        ),
        migrations.AlterUniqueTogether(
            name='sqlusernotification',
            unique_together=set([('user_id', 'msg')]),
        ),
    ]
