"""Models for dashboard application"""

import mongoengine
from xmodule.modulestore.mongoengine_fields import CourseKeyField


class CourseImportLog(mongoengine.Document):
    """Mongoengine model for git log"""
    course_id = CourseKeyField(max_length=128)
    # NOTE: this location is not a Location object but a pathname
    location = mongoengine.StringField(max_length=168)
    import_log = mongoengine.StringField(max_length=20 * 65535)
    git_log = mongoengine.StringField(max_length=65535)
    repo_dir = mongoengine.StringField(max_length=128)
    created = mongoengine.DateTimeField()
    meta = {'indexes': ['course_id', 'created'],
            'allow_inheritance': False}
