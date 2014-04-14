from django.db import models

class SeparatedValuesField(models.TextField):
    description = "Stores tags in a single database column."

    __metaclass__ = models.SubfieldBase

    def __init__(self, delimiter="|", *args, **kwargs):
        self.delimiter = delimiter
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.delimiter)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.delimiter.join([unicode(s) for s in value])

from south.modelsinspector import add_introspection_rules
add_introspection_rules([
    (
        [SeparatedValuesField], # Class(es) these apply to
        [],         # Positional arguments (not used)
        {           # Keyword argument
            "delimiter": ["delimiter", {"default": "|"}],
        },
    ),
], ["^bulk_email\.fields\.SeparatedValuesField"])