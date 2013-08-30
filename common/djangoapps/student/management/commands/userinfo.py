from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import json

from student.models import UserProfile


class Command(BaseCommand):
    help = \
''' Extract full user information into a JSON file.
Pass a single filename.'''

    def handle(self, *args, **options):
        f = open(args[0], 'w')
        #text = open(args[0]).read()
        #subject = open(args[1]).read()
        users = User.objects.all()

        l = []
        for user in users:
            up = UserProfile.objects.get(user=user)
            d = {'username': user.username,
                  'email': user.email,
                  'is_active': user.is_active,
                  'joined': user.date_joined.isoformat(),
                  'name': up.name,
                  'language': up.language,
                  'location': up.location}
            l.append(d)
        json.dump(l, f)
        f.close()
