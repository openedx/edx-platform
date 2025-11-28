# Migration to add TimeStampedModel fields to existing DiscussionModerationLog table

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('django_comment_common', '0010_discussion_muting_models'),
    ]

    operations = [
        # Add created and modified fields from TimeStampedModel
        migrations.AddField(
            model_name='discussionmoderationlog',
            name='created',
            field=model_utils.fields.AutoCreatedField(
                default=django.utils.timezone.now, 
                editable=False, 
                verbose_name='created'
            ),
        ),
        migrations.AddField(
            model_name='discussionmoderationlog',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(
                default=django.utils.timezone.now, 
                editable=False, 
                verbose_name='modified'
            ),
        ),
    ]