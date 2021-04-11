# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAuthorization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(unique=True, max_length=255, db_index=True)),
                ('email_enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(max_length=128, db_index=True)),
                ('subject', models.CharField(max_length=128, blank=True)),
                ('html_message', models.TextField(null=True, blank=True)),
                ('text_message', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('to_option', models.CharField(default=u'myself', max_length=64, choices=[(u'myself', u'Myself'), (u'staff', u'Staff and instructors'), (u'all', u'All')])),
                ('template_name', models.CharField(max_length=255, null=True)),
                ('from_addr', models.CharField(max_length=255, null=True)),
                ('sender', models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('html_template', models.TextField(null=True, blank=True)),
                ('plain_template', models.TextField(null=True, blank=True)),
                ('name', models.CharField(max_length=255, unique=True, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Optout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='optout',
            unique_together=set([('user', 'course_id')]),
        ),
    ]
