# -*- coding: utf-8 -*-



from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_goals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursegoal',
            name='goal_key',
            field=models.CharField(default=u'unsure', max_length=100, choices=[(u'certify', 'Earn a certificate'), (u'complete', 'Complete the course'), (u'explore', 'Explore the course'), (u'unsure', 'Not sure yet')]),
        ),
    ]
