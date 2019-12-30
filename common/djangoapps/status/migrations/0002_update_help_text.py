# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalstatusmessage',
            name='message',
            field=models.TextField(help_text=u'<p>The contents of this field will be displayed as a warning banner on all views.</p><p>To override the banner message for a specific course, refer to the Course Message configuration. Course Messages will only work if the global status message is enabled, so if you only want to add a banner to specific courses without adding a global status message, you should add a global status message with <strong>empty</strong> message text.</p><p>Finally, disable the global status message by adding another empty message with "enabled" unchecked.</p>', null=True, blank=True),
        ),
    ]
