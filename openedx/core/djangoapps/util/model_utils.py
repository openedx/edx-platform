class Creator(object):
    """
    A placeholder class that provides a way to set the attribute on the model.
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


class CreatorMixin(object):
    """
    Mixin class to provide SubfieldBase functionality to django fields.
    See: https://docs.djangoproject.com/en/1.11/releases/1.8/#subfieldbase
    """
    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(CreatorMixin, self).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, Creator(self))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)
