from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import contentstore.tasks

from pyftpdlib import ftpserver
import os

class DjangoAuthorizer(object):
    def validate_authentication(self, username, password):
        try: 
            u=User.objects.get(username=username)
        except User.DoesNotExist:
            return False
        # TODO: Check security groups
        return u.check_password(password)
    def has_user(self, username):
        print "????",username
        return True
    def has_perm(self, username, perm, path=None):
        print "!!!!!",username, perm, path
        return True
    def get_home_dir(self, username):
        d = "/tmp/ftp/"+username
        try: 
            os.mkdir(d)
        except OSError:
            pass
        return "/tmp/ftp/"+username
    def get_perms(self, username):
        return 'elradfmw'
    def get_msg_login(self, username):
        return 'Hello'
    def get_msg_quit(self, username):
        return 'Goodbye'
    def __init__(self):
        pass
    def impersonate_user(self, username, password):
        pass
    def terminate_impersonation(self, username):
        pass

def on_upload(ftp_handler, filename):
    source = ftp_handler.remote_ip
    author = ftp_handler.username
    print filename, author, source
    # We pass on this for now: 
    #   contentstore.tasks.on_upload
    # It is a changing API, and it makes testing the FTP server slow. 

class Command(BaseCommand):
    help = \
''' Run FTP server.'''
    def handle(self, *args, **options):
        authorizer = DjangoAuthorizer() #ftpserver.DummyAuthorizer()
        handler = ftpserver.FTPHandler
        handler.on_file_received = on_upload

        handler.authorizer = authorizer
        address = ("127.0.0.1", 2121)
        ftpd = ftpserver.FTPServer(address, handler)
        ftpd.serve_forever()
