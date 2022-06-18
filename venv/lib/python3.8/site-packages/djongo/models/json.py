import warnings

try:
    from jsoneditor.fields.django_jsonfield import JSONField as JSONFieldBase
except ImportError:
    from django.db import models

    class JSONFieldBase(models.TextField):

        def __init__(self, *args, **kwargs):
            warnings.warn(
                '"jsoneditor" module not available, to enable json mode '
                'please run: "pip install djongo[json]"', stacklevel=2)
            models.TextField.__init__(self, *args, **kwargs)


class JSONField(JSONFieldBase):

    def get_prep_value(self, value):
        return value
