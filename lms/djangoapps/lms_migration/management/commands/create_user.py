#!/usr/bin/python
#
# File:   create_user.py
#
# Create user.  Prompt for groups and ExternalAuthMap

import os
import sys
import string
import datetime
from getpass import getpass
import json
from random import choice
import readline

from django.core.management.base import BaseCommand
from student.models import UserProfile, Registration
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from django.contrib.auth.models import User, Group
from pytz import UTC


class MyCompleter(object):  # Custom completer

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [
                    option
                    for option in self.options
                    if option and option.startswith(text)
                ]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None


def GenPasswd(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for dummy0 in range(length)])

#-----------------------------------------------------------------------------
# main command


class Command(BaseCommand):
    help = "Create user, interactively; can add ExternalAuthMap for MIT user if email@MIT.EDU resolves properly."

    def handle(self, *args, **options):

        while True:
            uname = raw_input('username: ')
            if User.objects.filter(username=uname):
                print "username %s already taken" % uname
            else:
                break

        make_eamap = False
        if raw_input('Create MIT ExternalAuth? [n] ').lower() == 'y':
            email = '%s@MIT.EDU' % uname
            if not email.endswith('@MIT.EDU'):
                print "Failed - email must be @MIT.EDU"
                sys.exit(-1)
            mit_domain = 'ssl:MIT'
            if ExternalAuthMap.objects.filter(external_id=email, external_domain=mit_domain):
                print "Failed - email %s already exists as external_id" % email
                sys.exit(-1)
            make_eamap = True
            password = GenPasswd(12)

            # get name from kerberos
            try:
                kname = os.popen("finger %s | grep 'name:'" % email).read().strip().split('name: ')[1].strip()
            except:
                kname = ''
            name = raw_input('Full name: [%s] ' % kname).strip()
            if name == '':
                name = kname
            print "name = %s" % name
        else:
            while True:
                password = getpass()
                password2 = getpass()
                if password == password2:
                    break
                print "Oops, passwords do not match, please retry"

            while True:
                email = raw_input('email: ')
                if User.objects.filter(email=email):
                    print "email %s already taken" % email
                else:
                    break

            name = raw_input('Full name: ')

        user = User(username=uname, email=email, is_active=True)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            print "Oops, failed to create user %s, IntegrityError" % user
            raise

        r = Registration()
        r.register(user)

        up = UserProfile(user=user)
        up.name = name
        up.save()

        if make_eamap:
            credentials = "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN=%s/emailAddress=%s" % (name, email)
            eamap = ExternalAuthMap(
                external_id=email,
                external_email=email,
                external_domain=mit_domain,
                external_name=name,
                internal_password=password,
                external_credentials=json.dumps(credentials),
            )
            eamap.user = user
            eamap.dtsignup = datetime.datetime.now(UTC)
            eamap.save()

        print "User %s created successfully!" % user

        if not raw_input('Add user %s to any groups? [n] ' % user).lower() == 'y':
            sys.exit(0)

        print "Here are the groups available:"

        groups = [str(g.name) for g in Group.objects.all()]
        print groups

        completer = MyCompleter(groups)
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')

        while True:
            gname = raw_input("Add group (tab to autocomplete, empty line to end): ")
            if not gname:
                break
            if gname not in groups:
                print "Unknown group %s" % gname
                continue
            g = Group.objects.get(name=gname)
            user.groups.add(g)
            print "Added %s to group %s" % (user, g)

        print "Done!"
