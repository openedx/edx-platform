# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0013_delete_historical_enrollment_records'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollmentallowed',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text="First user which enrolled in the specified course through the specified e-mail. Once set, it won't change.", null=True, on_delete=models.CASCADE),
        ),
    ]
