# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from datetime import datetime

import os
import time
from django.db import migrations, models


def forwards(apps, schema_editor):
    """
    Migrate the initial badge classes, assertions, and course image configurations from certificates.
    """
    from django.core.files.base import ContentFile
    from xmodule.modulestore.django import modulestore
    from badges.events import course_complete
    classes = {}
    OldBadgeAssertion = apps.get_model("certificates", "BadgeAssertion")
    BadgeImageConfiguration = apps.get_model("certificates", "BadgeImageConfiguration")
    BadgeAssertion = apps.get_model("badges", "BadgeAssertion")
    BadgeClass = apps.get_model("badges", "BadgeClass")
    CourseCompleteImageConfiguration = apps.get_model("badges", "CourseCompleteImageConfiguration")
    for badge in OldBadgeAssertion.objects.all():
        if (badge.course_id, badge.mode) not in classes:
            course = modulestore().get_course(badge.course_id)
            image_config = BadgeImageConfiguration.objects.get(mode=badge.mode)
            icon = image_config.icon
            badge_class = BadgeClass(
                display_name=course.display_name,
                criteria=course_complete.evidence_url(badge.user_id, badge.course_id),
                description=course_complete.badge_description(course, badge.mode),
                slug=course_complete.course_slug(badge.course_id, badge.mode),
                mode=image_config.mode,
                course_id=badge.course_id,
            )
            file_content = ContentFile(icon.read())
            badge_class._meta.get_field('image').generate_filename = \
                lambda inst, fn: os.path.join('badge_classes', fn)
            badge_class.image.save(icon.name, file_content)
            badge_class.save()
            classes[(badge.course_id, badge.mode)] = badge_class
        if isinstance(badge.data, basestring):
            data = badge.data
        else:
            data = json.dumps(badge.data)
        assertion = BadgeAssertion(
            user_id=badge.user_id,
            badge_class=classes[(badge.course_id, badge.mode)],
            data=data,
            backend='BadgrBackend',
            image_url=badge.data['image'],
            assertion_url=badge.data['json']['id'],
        )
        assertion.save()
        # Would be overwritten by the first save.
        assertion.created = datetime.fromtimestamp(
            time.mktime(time.strptime(badge.data['created_at'], "%Y-%m-%dT%H:%M:%S"))
        )
        assertion.save()

    for configuration in BadgeImageConfiguration.objects.all():
        file_content = ContentFile(configuration.icon.read())
        new_conf = CourseCompleteImageConfiguration(
            default=configuration.default,
            mode=configuration.mode,
        )
        new_conf.icon.save(configuration.icon.name, file_content)
        new_conf.save()


def backwards(apps, schema_editor):
    from django.core.files.base import ContentFile
    OldBadgeAssertion = apps.get_model("certificates", "BadgeAssertion")
    BadgeAssertion = apps.get_model("badges", "BadgeAssertion")
    BadgeImageConfiguration = apps.get_model("certificates", "BadgeImageConfiguration")
    CourseCompleteImageConfiguration = apps.get_model("badges", "CourseCompleteImageConfiguration")
    for badge in BadgeAssertion.objects.all():
        if not badge.badge_class.mode:
            # Can't preserve old badges without modes.
            continue
        if isinstance(badge.data, basestring):
            data = badge.data
        else:
            data = json.dumps(badge.data)
        OldBadgeAssertion(
            user_id=badge.user_id,
            course_id=badge.badge_class.course_id,
            mode=badge.badge_class.mode,
            data=data,
        ).save()

    for configuration in CourseCompleteImageConfiguration.objects.all():
        file_content = ContentFile(configuration.icon.read())
        new_conf = BadgeImageConfiguration(
            default=configuration.default,
            mode=configuration.mode,
        )
        new_conf.icon.save(configuration.icon.name, file_content)
        new_conf.save()


class Migration(migrations.Migration):

    dependencies = [
        ('badges', '0001_initial'),
        ('certificates', '0003_data__default_modes')
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
