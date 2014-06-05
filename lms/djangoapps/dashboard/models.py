"""Models for dashboard application"""

import mongoengine


class CourseImportLog(mongoengine.Document):
    """Mongoengine model for git log"""
    # pylint: disable=R0924

    course_id = mongoengine.StringField(max_length=128)
    location = mongoengine.StringField(max_length=168)
    import_log = mongoengine.StringField(max_length=20 * 65535)
    git_log = mongoengine.StringField(max_length=65535)
    repo_dir = mongoengine.StringField(max_length=128)
    created = mongoengine.DateTimeField()
    meta = {'indexes': ['course_id', 'created'],
            'allow_inheritance': False}
