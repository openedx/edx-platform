# Generated manually to fix related_name conflicts
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('django_comment_common', '0010_discussion_muting_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discussionmoderationlog',
            name='moderator',
            field=models.ForeignKey(
                help_text='User performing the moderation action',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='discussion_moderation_logs',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='discussionmoderationlog',
            name='target_user',
            field=models.ForeignKey(
                help_text='User on whom the action was performed',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='discussion_moderation_targets',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]