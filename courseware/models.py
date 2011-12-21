from django.db import models
from django.contrib.auth.models import User

# class Organization(models.Model):
#     # Tree structure implemented such that child node has left ID 
#     # greater than all parents, and right ID less than all parents
#     left_tree_id = models.IntegerField(unique=True, db_index=True)
#     right_tree_id = models.IntegerField(unique=True, db_index=True)
#     # This is a duplicate, but we keep this to enforce unique name
#     # constraint
#     parent = models.ForeignKey('self', null=True, blank=True)
#     name = models.CharField(max_length=200)
#     ORG_TYPES= (('course','course'),
#                 ('chapter','chapter'),
#                 ('section','section'),)
#     org_type = models.CharField(max_length=32, choices=ORG_TYPES)
#     available = models.DateField(null=True, blank=True)
#     due = models.DateField(null=True, blank=True)
#     # JSON dictionary of metadata: 
#     # Time for a video, format of a section, etc. 
#     metadata = models.TextField(null=True, blank=True)

# class Modules(models.Model):
#     MOD_TYPES = (('hw','homework'),
#                  ('vid','video_clip'),
#                  ('lay','layout'),
#                  (),)
#     module_type = models.CharField(max_length=100)
#     left_tree_id = models.IntegerField(unique=True, db_index=True)
#     right_tree_id = models.IntegerField(unique=True, db_index=True)

#     LAYOUT_TYPES = (('leaf','leaf'),
#                     ('tab','tab'),
#                     ('seq','sequential'),
#                     ('sim','simultaneous'),)
#     layout_type = models.CharField(max_length=32, choices=LAYOUT_TYPES)
#     data = models.TextField(null=True, blank=True)

#class HomeworkProblems(models.Model):

class StudentModule(models.Model):
    # For a homework problem, contains a JSON
    # object consisting of state
    state = models.TextField(null=True, blank=True)
    grade = models.FloatField(null=True, blank=True)
    student = models.ForeignKey(User)
    MODULE_TYPES = (('problem','problem'),
                    ('video','video'),
                    ('html','html'),
                    )
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem')
    module_id = models.CharField(max_length=255) # Filename for homeworks, etc. 
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = (('student', 'module_id', 'module_type'),)

    def __unicode__(self):
        return self.module_type+'/'+self.student.username+"/"+self.module_id+'/'+str(self.state)[:20]
