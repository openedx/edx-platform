# -*- coding: utf-8 -*-
"""
Remaps all user anonymous ids
Must be called when django secret key was changed
"""

import hashlib
import json
import datetime
from django.core.management.base import BaseCommand, CommandError
from student.models import AnonymousUserId


class Command(BaseCommand):
    help = """Recreate anonymized ids when django secret key was changed"""
    can_import_settings = True

    def handle(self, *args, **options):
        from django.conf import settings
        secret_key = settings.SECRET_KEY
        qs = AnonymousUserId.objects.all()
        remaped = []
        for student in qs:
            hasher = hashlib.md5()
            hasher.update(secret_key)
            hasher.update(unicode(student.user.id))
            if student.course_id:
                hasher.update(
                    student.course_id.to_deprecated_string().encode('utf-8')
                )
            digest = hasher.hexdigest()
            if student.anonymous_user_id != digest:
                self.stdout.write(
                    "Saving new anonymous id value for user id `{}`".format(
                        student.user.id
                    )
                )
                old_id = student.anonymous_user_id
                student.anonymous_user_id = digest
                student.save()
                remaped.append({
                    "old_id": old_id,
                    "new_id": digest,
                    "email": student.user.email,
                    "course_id": student.course_id.to_deprecated_string()
                        .encode('utf-8') if student.course_id else ""
                })
        filename = "anonymous_ids-{}.json".format(datetime.datetime.now())
        with open(filename, 'w') as outfile:
            json.dump({"dump": remaped}, outfile)
        self.stdout.write(
            "{} ids were changed of total {}".format(len(remaped), qs.count())
        )
