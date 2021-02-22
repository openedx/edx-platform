# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_course_key_field_to_foreign_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('platform', models.CharField(max_length=30)),
                ('social_link', models.CharField(max_length=100, blank=True)),
                ('user_profile', models.ForeignKey(related_name='social_links', to='student.UserProfile', on_delete=models.CASCADE)),
            ],
        ),
    ]
