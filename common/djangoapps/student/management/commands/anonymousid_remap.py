# -*- coding: utf-8 -*-
"""
Remaps all user anonymous ids
Must be called when django secret key was changed
"""

import hashlib
from django.core.management.base import BaseCommand, CommandError
from student.models import AnonymousUserId


class Command(BaseCommand):

    help = """Recreate anonymized ids when django secret key was changed"""
    can_import_settings = True

    def handle(self, *args, **options):
        from django.conf import settings
        secret_key = settings.SECRET_KEY
        qs = AnonymousUserId.objects.all()
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
                student.anonymous_user_id = digest
                student.save()
