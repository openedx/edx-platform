from django.db import models

class JabberUser(models.Model):
    class Meta:
        app_label = 'jabber'
        db_table = 'users'

    # This is the primary key for our table, since ejabberd doesn't
    # put an ID column on this table. This will match the edX
    # username chosen by the user.
    username = models.CharField(max_length=255, db_index=True, primary_key=True)

    # Yes, this is stored in plaintext. ejabberd only knows how to do
    # basic string matching, so we don't hash/salt this or anything.
    password = models.TextField(default="")

    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
