"""
Initial migration for AI Learning models.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIGeneratedCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, help_text='Course identifier', max_length=255, unique=True)),
                ('generation_prompt', models.TextField(help_text='Original prompt used to generate the course')),
                ('curriculum_data', models.JSONField(default=dict, help_text='Structured curriculum data from AI Engine')),
                ('generation_status', models.CharField(choices=[('pending', 'Pending'), ('generating', 'Generating'), ('completed', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', help_text='Current status of course generation', max_length=20)),
                ('ai_engine_course_id', models.CharField(db_index=True, help_text='Course ID in the AI Engine system', max_length=255)),
                ('metadata', models.JSONField(default=dict, help_text='Additional metadata about the course generation')),
                ('creator', models.ForeignKey(help_text='User who requested the course generation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_generated_courses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'AI Generated Course',
                'verbose_name_plural': 'AI Generated Courses',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='StudentLearningProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('ai_engine_profile_id', models.CharField(db_index=True, help_text='Profile ID in the AI Engine system', max_length=255, unique=True)),
                ('learning_style', models.CharField(blank=True, help_text='Identified learning style (visual, auditory, kinesthetic, etc.)', max_length=50)),
                ('mastered_concepts', models.JSONField(default=list, help_text='List of concepts the student has mastered')),
                ('struggling_concepts', models.JSONField(default=list, help_text='List of concepts the student is struggling with')),
                ('preferences', models.JSONField(default=dict, help_text='Student learning preferences')),
                ('last_sync', models.DateTimeField(auto_now=True, help_text='Last time profile was synced with AI Engine')),
                ('user', models.OneToOneField(help_text='Student user account', on_delete=django.db.models.deletion.CASCADE, related_name='ai_learning_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Student Learning Profile',
                'verbose_name_plural': 'Student Learning Profiles',
            },
        ),
        migrations.CreateModel(
            name='AdaptiveInteraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, help_text='Course where interaction occurred', max_length=255)),
                ('usage_key', opaque_keys.edx.django.models.UsageKeyField(db_index=True, help_text='Specific XBlock where interaction occurred', max_length=255)),
                ('interaction_type', models.CharField(choices=[('assessment', 'Assessment'), ('tutor_chat', 'Tutor Chat'), ('content_view', 'Content View'), ('adaptation', 'Adaptation')], db_index=True, help_text='Type of adaptive interaction', max_length=50)),
                ('interaction_data', models.JSONField(default=dict, help_text='Data about the interaction')),
                ('ai_response', models.JSONField(default=dict, help_text='Response from AI Engine')),
                ('response_time_ms', models.IntegerField(blank=True, help_text='Time taken for AI Engine to respond (milliseconds)', null=True)),
                ('user', models.ForeignKey(help_text='Student who performed the interaction', on_delete=django.db.models.deletion.CASCADE, related_name='adaptive_interactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Adaptive Interaction',
                'verbose_name_plural': 'Adaptive Interactions',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='AIEngineWebhook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('webhook_type', models.CharField(db_index=True, help_text='Type of webhook event', max_length=50)),
                ('payload', models.JSONField(help_text='Webhook payload data')),
                ('status', models.CharField(choices=[('received', 'Received'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], db_index=True, default='received', help_text='Processing status', max_length=20)),
                ('error_message', models.TextField(blank=True, help_text='Error message if processing failed')),
            ],
            options={
                'verbose_name': 'AI Engine Webhook',
                'verbose_name_plural': 'AI Engine Webhooks',
                'ordering': ['-created'],
            },
        ),
        migrations.AddIndex(
            model_name='adaptiveinteraction',
            index=models.Index(fields=['user', 'course_key', '-created'], name='ai_learning_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='adaptiveinteraction',
            index=models.Index(fields=['interaction_type', '-created'], name='ai_learning_interac_idx'),
        ),
    ]
