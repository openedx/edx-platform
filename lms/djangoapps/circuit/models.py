from django.db import models


class ServerCircuit(models.Model):
    # Later, add owner, who can edit, part of what app, etc.
    name = models.CharField(max_length=32, unique=True, db_index=True)
    schematic = models.TextField(blank=True)

    def __unicode__(self):
        return self.name + ":" + self.schematic[:8]
