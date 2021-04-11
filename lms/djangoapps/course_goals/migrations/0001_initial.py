# -*- coding: utf-8 -*-



from django.db import migrations, models
from django.conf import settings
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
                ('goal_key', models.CharField(default=u'unsure', max_length=100, choices=[(u'certify', 'Earn a certificate.'), (u'complete', 'Complete the course.'), (u'explore', 'Explore the course.'), (u'unsure', 'Not sure yet.')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursegoal',
            unique_together=set([('user', 'course_key')]),
        ),
    ]
