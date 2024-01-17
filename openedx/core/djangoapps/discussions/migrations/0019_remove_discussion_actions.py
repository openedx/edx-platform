from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
       ('discussions', '0018_discussionTag'),
    ]

    operations = [
        migrations.DeleteModel(
            name='discussionActions',
        ),
    ]
