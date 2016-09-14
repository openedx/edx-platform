# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PuzzleComplete',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unique_user_id', models.CharField(max_length=50, db_index=True)),
                ('puzzle_id', models.IntegerField()),
                ('puzzle_set', models.IntegerField(db_index=True)),
                ('puzzle_subset', models.IntegerField(db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='foldit_puzzles_complete', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['puzzle_id'],
            },
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unique_user_id', models.CharField(max_length=50, db_index=True)),
                ('puzzle_id', models.IntegerField()),
                ('best_score', models.FloatField(db_index=True)),
                ('current_score', models.FloatField(db_index=True)),
                ('score_version', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='foldit_scores', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='puzzlecomplete',
            unique_together=set([('user', 'puzzle_id', 'puzzle_set', 'puzzle_subset')]),
        ),
    ]
