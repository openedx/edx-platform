"""
Base objects that data.py uses
"""

import json
import inspect
import dateutil.parser
import copy
from datetime import datetime, timedelta
from freezegun.api import FakeDatetime


class DateTimeWithDeltaCompare(datetime):
    """
    Create a subclass of datetime with special equality methods
    that treat very, very similar datetimes as 'equal'. This is helpful
    to account for slight timestamp quantization/skews that happen when writing a
    datetime object to a database and reading it back
    """

    _max_allowed_time_diff = timedelta(0, 0, 10000)  # max tolerance 10ms

    def __eq__(self, other):
        """
        If two datetimes are within 10ms of each other then consider them equal
        """

        diff = self - other if self > other else other - self
        return diff <= self._max_allowed_time_diff

    def __ne__(self, other):
        """
        If two datetimes are within 10ms of each other then consider them equal
        """

        diff = self - other if self > other else other - self

        return diff > self._max_allowed_time_diff


class Dict(dict):
    """
    Create a subclass of dict to make it weak referencable
    per https://docs.python.org/2/library/weakref.html
    """
    pass


class TypedField(object):
    """
    Field Decscriptors used to enforce correct typing
    """

    _expected_types = None
    __name__ = None

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Initializer which takes in the type this field
        should be set it is set
        """

        if not self._expected_types:
            raise TypeError(
                "Subclass of TypedField ('{type_name}') has not set required "
                "_expected_types attribute".format(type_name=type(self).__name__)
            )

        self._default = kwargs.get('default', None)

    def _assert_has_name(self):
        """
        Helper method to make sure we have our __name__ attribute
        set before we do any reads/writes
        """

    def __get__(self, data_object, owner_class):
        """
        Descriptor getter
        """
        if not data_object:
            # called as a class method, so return the descriptor (ourselves)
            return self

        self._assert_has_name()

        if not hasattr(data_object, '_field_data'):
            return self._default

        return data_object._field_data.get(self.__name__, self._default)  # pylint: disable=protected-access

    def __set__(self, data_object, value):
        """
        Descriptor setter. Be sure to enforce type on setting. But None is allowed.
        """

        self._assert_has_name()

        value_type = type(value)

        if value and value_type not in self._expected_types:
            raise TypeError(
                (
                    "Field expected type of '{expected}' got '{got}'"
                ).format(expected=self._expected_types, got=value_type)
            )

        if not hasattr(data_object, '_field_data'):
            data_object._field_data = {}  # pylint: disable=protected-access

        data_object._field_data[self.__name__] = value  # pylint: disable=protected-access

    def __delete__(self, data_object):
        """
        Descriptor delete
        """

        self._assert_has_name()

        if hasattr(data_object, '_field_data') and self.__name__ in data_object._field_data:  # pylint: disable=protected-access
            del data_object._field_data[self.__name__]  # pylint: disable=protected-access


class StringField(TypedField):
    """
    Specialized subclass of TypedField(unicode) as a convienence
    """

    _expected_types = [unicode, str]


class IntegerField(TypedField):
    """
    Specialized subclass of TypedField(int) as a convienence
    """

    _expected_types = [int, long]


class BooleanField(TypedField):
    """
    Specialized subclass of TypedField(bool) as a convienence
    """

    _expected_types = [bool]


class DictField(TypedField):
    """
    Specialized subclass of TypedField(dict) as a convienence
    """

    _expected_types = [dict]

    @classmethod
    def to_json(cls, data):
        """
        Serialize to json
        """

        if not data:
            return None

        def datetime_to_json(obj):
            """
            JSON serializer for objects not serializable by default json code.
            For now, this means datetime objects.
            """

            if isinstance(obj, datetime):
                serial = obj.isoformat()
                return serial

            raise TypeError(
                "Could not provide JSON serializer for type {name}!".format(name=type(obj))
            )

        return json.dumps(data, default=datetime_to_json)

    @classmethod
    def from_json(cls, value):
        """
        Deserialize from json
        """

        if not value:
            return None

        _dict = json.loads(value)

        for key, value in _dict.iteritems():
            if isinstance(value, basestring):
                # This could be a datetime posing as a ISO8601 formatted string
                # we so have to apply some heuristics here
                # to see if we want to even attempt
                might_be_datetime = (
                    value.count('-') == 2 and
                    (value.count(':') == 2 or value.count(':') == 3) and
                    value.count('T') == 1
                )
                if might_be_datetime:
                    # this is likely a ISO8601 serialized string, so let's try to parse
                    try:
                        _dict[key] = dateutil.parser.parse(value)
                    except ValueError:
                        # oops, I guess our heuristic was a bit off
                        # no harm, but just wasted CPU cycles
                        pass

        return _dict


class DateTimeField(TypedField):
    """
    Specialized subclass of TypedField(datetime) as a convienence
    """

    _expected_types = [datetime, FakeDatetime]


class EnumField(StringField):
    """
    Specialized subclass of TypedField() which is basically an StringTypedField,
    but constrains what values can be set on it
    """

    def __init__(self, **kwargs):
        """
        Initializer with constrained values
        """

        self._allowed_values = kwargs['allowed_values']
        super(EnumField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        """
        Descriptor setter. Be sure to enforce type on setting. But None is allowed.
        """

        if self._allowed_values:
            if value not in self._allowed_values:
                msg = (
                    "Attempting to set to '{value}'. Allowed values are: '{allowed}'."
                ).format(value=value, allowed=str(self._allowed_values))
                raise ValueError(msg)

        super(EnumField, self).__set__(instance, value)


class BaseDataObjectMetaClass(type):
    """
    A metaclass which adds the __name__ attribute to all TypedField descriptors. We
    need to do this because we store the values of the descriptors in a dictionary on
    the instance itself, therefore it needs to know the attribute name it is bound
    to in the containing object
    """
    def __new__(mcs, name, bases, attrs):
        # Iterate over the TypedField attrs before they're bound to the class
        # so that we don't accidentally trigger any __get__ methods
        for attr_name, attr in attrs.iteritems():
            if isinstance(attr, TypedField):
                attr.__name__ = attr_name

        # Do the same with any other base classes
        for base in bases:
            for attr_name, attr in inspect.getmembers(base, lambda attr: isinstance(attr, TypedField)):
                attr.__name__ = attr_name

        return super(BaseDataObjectMetaClass, mcs).__new__(mcs, name, bases, attrs)


class BaseDataObject(object):
    """
    A base class for all Notification Data Objects
    """

    # assign a metaclass so that all TypedFields in a BaseDataObject derviced class get a
    # __name__ attribute set which is the attribute name in the containing object
    __metaclass__ = BaseDataObjectMetaClass

    id = IntegerField(name='id', default=None)  # pylint: disable=invalid-name

    def __init__(self, **kwargs):
        """
        Initializer which will allow for kwargs. Note we can only allow for setting
        of attributes which have been explicitly declared in any subclass
        """

        for key in kwargs.keys():
            value = kwargs[key]
            if key in dir(self):
                setattr(self, key, value)
            else:
                raise ValueError(
                    (
                        "Initialization parameter '{name}' was passed in although "
                        "it is not a known field to the DataObject."
                    ).format(name=key)
                )

    def __setattr__(self, attribute, value):
        """
        Don't allow new attributes to be added outside of
        attributes that were present after initialization
        We want our data models to have a schema that is fixed as design time!!!
        """

        if attribute != '_field_data' and attribute not in dir(self):
            raise ValueError(
                (
                    "Attempting to add a new attribute '{name}' that was not part of "
                    "the original schema."
                ).format(name=attribute)
            )

        super(BaseDataObject, self).__setattr__(attribute, value)

    def __eq__(self, other):
        """
        Equality test - simply compare all of the fields
        """

        # pylint disable this because self & other are the same class types
        _self_fields = self._get_fields_for_equality_check()
        _other_fields = other._get_fields_for_equality_check()  # pylint: disable=protected-access

        return _self_fields == _other_fields

    def __ne__(self, other):
        """
        Inequality test - simply compare all of the fields
        """

        # pylint disable this because self & other are the same class types
        _self_fields = self._get_fields_for_equality_check()
        _other_fields = other._get_fields_for_equality_check()  # pylint: disable=protected-access

        return _self_fields != _other_fields

    def __str__(self):
        """
        Dump out all of our fields
        """

        return str(self.get_fields())

    def __unicode__(self):
        """
        Dump out all of our fields
        """

        return unicode(self.get_fields())

    @classmethod
    def clone(cls, src):
        """
        Create a cloned object
        """

        instance = cls()
        for attr_name, __ in inspect.getmembers(cls, lambda attr: isinstance(attr, TypedField)):
            if hasattr(src, attr_name):
                val = getattr(src, attr_name)
                # when cloning a dict, make a copy
                # in case caller alters it
                if isinstance(val, dict):
                    val = copy.deepcopy(val)

                setattr(instance, attr_name, val)

        return instance

    def get_fields(self):
        """
        Returns all fields as a dict. This will include any sub objects
        """

        _dict = {}
        for attr_name, __ in inspect.getmembers(self.__class__, lambda attr: isinstance(attr, TypedField)):
            value = getattr(self, attr_name)
            if isinstance(value, BaseDataObject):
                _dict[attr_name] = value.get_fields()
            else:
                _dict[attr_name] = value
        return _dict

    def _get_fields_for_equality_check(self):
        """
        Returns all fields as a dict but use a specialized datetime subclass that allows
        for some limited tolerances regarding tests for equality
        """

        _dict = {}
        for attr_name, __ in inspect.getmembers(self.__class__, lambda attr: isinstance(attr, TypedField)):
            value = getattr(self, attr_name)

            if isinstance(value, BaseDataObject):
                # disable pylint error because we are calling a objects of the same base class
                _dict[attr_name] = value._get_fields_for_equality_check()  # pylint: disable=protected-access
            elif isinstance(value, datetime):
                _dict[attr_name] = DateTimeWithDeltaCompare(
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond
                )
            else:
                _dict[attr_name] = value
        return _dict

    def validate(self):
        """
        This should be overriden to do real validation.
        Validations should throw a ValidationError if there
        is a problem.
        """
        pass  # this intentionally does nothing


class RelatedObjectField(TypedField):
    """
    This field is a related object that is joined to the containing object,
    for example a foreign key. The related object must be of type BaseDataObject
    """

    def __init__(self, related_type, **kwargs):
        """
        Initializer for related object which must be a subclass of
        BaseDataObject
        """

        if not issubclass(related_type, BaseDataObject):
            msg = (
                "Creating a related field of type '{name}' which is not a "
                "subclass of BaseDataObject."
            ).format(name=related_type)

            raise TypeError(msg)

        self._expected_types = [related_type]

        super(RelatedObjectField, self).__init__(**kwargs)
