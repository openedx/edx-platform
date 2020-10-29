# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0007_courseoverviewimageconfig'),
    ]

    operations = [
        # Removed because we accidentally removed this column without first
        # removing the code that refers to this.  This can cause errors in production.
    ]
