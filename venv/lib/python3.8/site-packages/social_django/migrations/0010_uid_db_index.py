from django.conf import settings
from django.db import models, migrations

from social_core.utils import setting_name

UID_LENGTH = getattr(settings, setting_name('UID_LENGTH'), 255)


class Migration(migrations.Migration):
    dependencies = [
        ('social_django', '0009_auto_20191118_0520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersocialauth',
            name='uid',
            field=models.CharField(max_length=UID_LENGTH, db_index=True),
        ),
    ]
