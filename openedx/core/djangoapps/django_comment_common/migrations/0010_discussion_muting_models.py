# Generated manually - add discussion muting models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('django_comment_common', '0009_coursediscussionsettings_reported_content_email_notifications'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscussionMute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(help_text='Course in which mute applies', max_length=255)),
                ('scope', models.CharField(choices=[('personal', 'Personal'), ('course', 'Course-wide')], default='personal', help_text='Scope of the mute (personal or course-wide)', max_length=10)),
                ('reason', models.TextField(blank=True, help_text='Optional reason for muting')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the mute is currently active')),
                ('muted_at', models.DateTimeField(auto_now_add=True)),
                ('unmuted_at', models.DateTimeField(blank=True, null=True)),
                ('muted_by', models.ForeignKey(help_text='User performing the mute', on_delete=django.db.models.deletion.CASCADE, related_name='muted_users', to=settings.AUTH_USER_MODEL)),
                ('muted_user', models.ForeignKey(help_text='User being muted', on_delete=django.db.models.deletion.CASCADE, related_name='muted_by_users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['muted_user', 'course_id', 'is_active'], name='django_comment_muted_user_course_active_idx'),
                    models.Index(fields=['muted_by', 'course_id', 'scope'], name='django_comment_muted_by_course_scope_idx'),
                ],
                'unique_together': {('muted_user', 'muted_by', 'course_id', 'scope')},
            },
        ),
        migrations.CreateModel(
            name='DiscussionMuteException',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(help_text='Course where the exception applies', max_length=255)),
                ('exception_user', models.ForeignKey(help_text='User who unmuted the muted_user for themselves', on_delete=django.db.models.deletion.CASCADE, related_name='mute_exceptions', to=settings.AUTH_USER_MODEL)),
                ('muted_user', models.ForeignKey(help_text='User who is globally muted in this course', on_delete=django.db.models.deletion.CASCADE, related_name='mute_exceptions_for', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['muted_user', 'course_id'], name='django_comment_mute_exception_user_course_idx'),
                    models.Index(fields=['exception_user', 'course_id'], name='django_comment_mute_exception_exception_user_idx'),
                ],
                'unique_together': {('muted_user', 'exception_user', 'course_id')},
            },
        ),
        migrations.CreateModel(
            name='DiscussionModerationLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('action_type', models.CharField(choices=[('mute', 'Mute'), ('unmute', 'Unmute'), ('mute_and_report', 'Mute and Report')], help_text='Type of moderation action performed', max_length=20)),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(help_text='Course where the action was performed', max_length=255)),
                ('scope', models.CharField(choices=[('personal', 'Personal'), ('course', 'Course-wide')], default='personal', help_text='Scope of the moderation action', max_length=10)),
                ('reason', models.TextField(blank=True, help_text='Optional reason for moderation')),
                ('metadata', jsonfield.fields.JSONField(blank=True, default=dict, help_text='Additional metadata for the action')),
                ('moderator', models.ForeignKey(help_text='User performing the moderation action', on_delete=django.db.models.deletion.CASCADE, related_name='moderation_logs', to=settings.AUTH_USER_MODEL)),
                ('target_user', models.ForeignKey(help_text='User on whom the action was performed', on_delete=django.db.models.deletion.CASCADE, related_name='moderation_actions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['target_user', 'course_id', 'created'], name='django_comment_moderation_log_target_course_created_idx'),
                    models.Index(fields=['moderator', 'course_id', 'action_type'], name='django_comment_moderation_log_moderator_course_action_idx'),
                    models.Index(fields=['course_id', 'action_type', 'created'], name='django_comment_moderation_log_course_action_created_idx'),
                ],
            },
        ),
    ]