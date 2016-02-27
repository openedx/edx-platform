# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, OperationalError, connection
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0008_remove_courseoverview_facebook_url'),
    ]

    # An original version of 0008 removed the facebook_url field
    # We need to handle the case where our noop 0008 ran AND the case
    # where the original 0008 ran.  We do that by using Django's introspection
    # API to query INFORMATION_SCHEMA.  _meta is unavailable as the
    # column has already been removed from the model.
    fields = connection.introspection.get_table_description(connection.cursor(),'course_overviews_courseoverview')
    operations = []

    if not any(f.name == 'facebook_url' for f in fields):
        operations += migrations.AddField(
            model_name='courseoverview',
            name='facebook_url',
            field=models.TextField(null=True),
        ),
