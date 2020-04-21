# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verified_track_content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='verifiedtrackcohortedcourse',
            name='verified_cohort_name',
            field=models.CharField(default=u'Verified Learners', max_length=100),
        ),
    ]
