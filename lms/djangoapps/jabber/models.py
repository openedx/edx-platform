from django.db import models

class JabberUser(models.Model):
    # The default length of the Jabber passwords we create. We set a
    # really long default since we're storing these passwords in
    # plaintext (ejabberd implementation detail).
    DEFAULT_PASSWORD_LENGTH = 256

    class Meta:
        app_label = u'jabber'
        db_table = u'users'

    # This is the primary key for our table, since ejabberd doesn't
    # put an ID column on this table. This will match the edX
    # username chosen by the user.
    username = models.CharField(max_length=250, primary_key=True)

    # Yes, this is stored in plaintext. ejabberd only knows how to do
    # basic string matching, so we don't hash/salt this or anything.
    password = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, null=True)
