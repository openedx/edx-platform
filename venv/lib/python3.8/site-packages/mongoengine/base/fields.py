import operator
import weakref

import pymongo
from bson import SON, DBRef, ObjectId

from mongoengine.base.common import UPDATE_OPERATORS
from mongoengine.base.datastructures import (
    BaseDict,
    BaseList,
    EmbeddedDocumentList,
)
from mongoengine.common import _import_class
from mongoengine.errors import DeprecatedError, ValidationError

__all__ = ("BaseField", "ComplexBaseField", "ObjectIdField", "GeoJsonBaseField")


class BaseField:
    """A base class for fields in a MongoDB document. Instances of this class
    may be added to subclasses of `Document` to define a document's schema.
    """

    name = None  # set in TopLevelDocumentMetaclass
    _geo_index = False
    _auto_gen = False  # Call `generate` to generate a value
    _auto_dereference = True

    # These track each time a Field instance is created. Used to retain order.
    # The auto_creation_counter is used for fields that MongoEngine implicitly
    # creates, creation_counter is used for all user-specified fields.
    creation_counter = 0
    auto_creation_counter = -1

    def __init__(
        self,
        db_field=None,
        required=False,
        default=None,
        unique=False,
        unique_with=None,
        primary_key=False,
        validation=None,
        choices=None,
        null=False,
        sparse=False,
        **kwargs,
    ):
        """
        :param db_field: The database field to store this field in
            (defaults to the name of the field)
        :param required: If the field is required. Whether it has to have a
            value or not. Defaults to False.
        :param default: (optional) The default value for this field if no value
            has been set (or if the value has been unset).  It can be a
            callable.
        :param unique: Is the field value unique or not.  Defaults to False.
        :param unique_with: (optional) The other field this field should be
            unique with.
        :param primary_key: Mark this field as the primary key. Defaults to False.
        :param validation: (optional) A callable to validate the value of the
            field.  The callable takes the value as parameter and should raise
            a ValidationError if validation fails
        :param choices: (optional) The valid choices
        :param null: (optional) If the field value can be null. If no and there is a default value
            then the default value is set
        :param sparse: (optional) `sparse=True` combined with `unique=True` and `required=False`
            means that uniqueness won't be enforced for `None` values
        :param **kwargs: (optional) Arbitrary indirection-free metadata for
            this field can be supplied as additional keyword arguments and
            accessed as attributes of the field. Must not conflict with any
            existing attributes. Common metadata includes `verbose_name` and
            `help_text`.
        """
        self.db_field = db_field if not primary_key else "_id"

        self.required = required or primary_key
        self.default = default
        self.unique = bool(unique or unique_with)
        self.unique_with = unique_with
        self.primary_key = primary_key
        self.validation = validation
        self.choices = choices
        self.null = null
        self.sparse = sparse
        self._owner_document = None

        # Make sure db_field is a string (if it's explicitly defined).
        if self.db_field is not None and not isinstance(self.db_field, str):
            raise TypeError("db_field should be a string.")

        # Make sure db_field doesn't contain any forbidden characters.
        if isinstance(self.db_field, str) and (
            "." in self.db_field
            or "\0" in self.db_field
            or self.db_field.startswith("$")
        ):
            raise ValueError(
                'field names cannot contain dots (".") or null characters '
                '("\\0"), and they must not start with a dollar sign ("$").'
            )

        # Detect and report conflicts between metadata and base properties.
        conflicts = set(dir(self)) & set(kwargs)
        if conflicts:
            raise TypeError(
                "%s already has attribute(s): %s"
                % (self.__class__.__name__, ", ".join(conflicts))
            )

        # Assign metadata to the instance
        # This efficient method is available because no __slots__ are defined.
        self.__dict__.update(kwargs)

        # Adjust the appropriate creation counter, and save our local copy.
        if self.db_field == "_id":
            self.creation_counter = BaseField.auto_creation_counter
            BaseField.auto_creation_counter -= 1
        else:
            self.creation_counter = BaseField.creation_counter
            BaseField.creation_counter += 1

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        return instance._data.get(self.name)

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document."""
        # If setting to None and there is a default value provided for this
        # field, then set the value to the default value.
        if value is None:
            if self.null:
                value = None
            elif self.default is not None:
                value = self.default
                if callable(value):
                    value = value()

        if instance._initialised:
            try:
                value_has_changed = (
                    self.name not in instance._data
                    or instance._data[self.name] != value
                )
                if value_has_changed:
                    instance._mark_as_changed(self.name)
            except Exception:
                # Some values can't be compared and throw an error when we
                # attempt to do so (e.g. tz-naive and tz-aware datetimes).
                # Mark the field as changed in such cases.
                instance._mark_as_changed(self.name)

        EmbeddedDocument = _import_class("EmbeddedDocument")
        if isinstance(value, EmbeddedDocument):
            value._instance = weakref.proxy(instance)
        elif isinstance(value, (list, tuple)):
            for v in value:
                if isinstance(v, EmbeddedDocument):
                    v._instance = weakref.proxy(instance)

        instance._data[self.name] = value

    def error(self, message="", errors=None, field_name=None):
        """Raise a ValidationError."""
        field_name = field_name if field_name else self.name
        raise ValidationError(message, errors=errors, field_name=field_name)

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        return value

    def to_mongo(self, value):
        """Convert a Python type to a MongoDB-compatible type."""
        return self.to_python(value)

    def _to_mongo_safe_call(self, value, use_db_field=True, fields=None):
        """Helper method to call to_mongo with proper inputs."""
        f_inputs = self.to_mongo.__code__.co_varnames
        ex_vars = {}
        if "fields" in f_inputs:
            ex_vars["fields"] = fields

        if "use_db_field" in f_inputs:
            ex_vars["use_db_field"] = use_db_field

        return self.to_mongo(value, **ex_vars)

    def prepare_query_value(self, op, value):
        """Prepare a value that is being used in a query for PyMongo."""
        if op in UPDATE_OPERATORS:
            self.validate(value)
        return value

    def validate(self, value, clean=True):
        """Perform validation on a value."""
        pass

    def _validate_choices(self, value):
        Document = _import_class("Document")
        EmbeddedDocument = _import_class("EmbeddedDocument")

        choice_list = self.choices
        if isinstance(next(iter(choice_list)), (list, tuple)):
            # next(iter) is useful for sets
            choice_list = [k for k, _ in choice_list]

        # Choices which are other types of Documents
        if isinstance(value, (Document, EmbeddedDocument)):
            if not any(isinstance(value, c) for c in choice_list):
                self.error("Value must be an instance of %s" % (choice_list))
        # Choices which are types other than Documents
        else:
            values = value if isinstance(value, (list, tuple)) else [value]
            if len(set(values) - set(choice_list)):
                self.error("Value must be one of %s" % str(choice_list))

    def _validate(self, value, **kwargs):
        # Check the Choices Constraint
        if self.choices:
            self._validate_choices(value)

        # check validation argument
        if self.validation is not None:
            if callable(self.validation):
                try:
                    # breaking change of 0.18
                    # Get rid of True/False-type return for the validation method
                    # in favor of having validation raising a ValidationError
                    ret = self.validation(value)
                    if ret is not None:
                        raise DeprecatedError(
                            "validation argument for `%s` must not return anything, "
                            "it should raise a ValidationError if validation fails"
                            % self.name
                        )
                except ValidationError as ex:
                    self.error(str(ex))
            else:
                raise ValueError(
                    'validation argument for `"%s"` must be a ' "callable." % self.name
                )

        self.validate(value, **kwargs)

    @property
    def owner_document(self):
        return self._owner_document

    def _set_owner_document(self, owner_document):
        self._owner_document = owner_document

    @owner_document.setter
    def owner_document(self, owner_document):
        self._set_owner_document(owner_document)


class ComplexBaseField(BaseField):
    """Handles complex fields, such as lists / dictionaries.

    Allows for nesting of embedded documents inside complex types.
    Handles the lazy dereferencing of a queryset by lazily dereferencing all
    items in a list / dict rather than one at a time.
    """

    def __init__(self, field=None, **kwargs):
        self.field = field
        super().__init__(**kwargs)

    @staticmethod
    def _lazy_load_refs(instance, name, ref_values, *, max_depth):
        _dereference = _import_class("DeReference")()
        documents = _dereference(
            ref_values,
            max_depth=max_depth,
            instance=instance,
            name=name,
        )
        return documents

    def __get__(self, instance, owner):
        """Descriptor to automatically dereference references."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        ReferenceField = _import_class("ReferenceField")
        GenericReferenceField = _import_class("GenericReferenceField")
        EmbeddedDocumentListField = _import_class("EmbeddedDocumentListField")

        auto_dereference = instance._fields[self.name]._auto_dereference

        dereference = auto_dereference and (
            self.field is None
            or isinstance(self.field, (GenericReferenceField, ReferenceField))
        )

        if (
            instance._initialised
            and dereference
            and instance._data.get(self.name)
            and not getattr(instance._data[self.name], "_dereferenced", False)
        ):
            ref_values = instance._data.get(self.name)
            instance._data[self.name] = self._lazy_load_refs(
                ref_values=ref_values, instance=instance, name=self.name, max_depth=1
            )
            if hasattr(instance._data[self.name], "_dereferenced"):
                instance._data[self.name]._dereferenced = True

        value = super().__get__(instance, owner)

        # Convert lists / values so we can watch for any changes on them
        if isinstance(value, (list, tuple)):
            if issubclass(type(self), EmbeddedDocumentListField) and not isinstance(
                value, EmbeddedDocumentList
            ):
                value = EmbeddedDocumentList(value, instance, self.name)
            elif not isinstance(value, BaseList):
                value = BaseList(value, instance, self.name)
            instance._data[self.name] = value
        elif isinstance(value, dict) and not isinstance(value, BaseDict):
            value = BaseDict(value, instance, self.name)
            instance._data[self.name] = value

        if (
            auto_dereference
            and instance._initialised
            and isinstance(value, (BaseList, BaseDict))
            and not value._dereferenced
        ):
            value = self._lazy_load_refs(
                ref_values=value, instance=instance, name=self.name, max_depth=1
            )
            value._dereferenced = True
            instance._data[self.name] = value

        return value

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        if isinstance(value, str):
            return value

        if hasattr(value, "to_python"):
            return value.to_python()

        BaseDocument = _import_class("BaseDocument")
        if isinstance(value, BaseDocument):
            # Something is wrong, return the value as it is
            return value

        is_list = False
        if not hasattr(value, "items"):
            try:
                is_list = True
                value = {idx: v for idx, v in enumerate(value)}
            except TypeError:  # Not iterable return the value
                return value

        if self.field:
            self.field._auto_dereference = self._auto_dereference
            value_dict = {
                key: self.field.to_python(item) for key, item in value.items()
            }
        else:
            Document = _import_class("Document")
            value_dict = {}
            for k, v in value.items():
                if isinstance(v, Document):
                    # We need the id from the saved object to create the DBRef
                    if v.pk is None:
                        self.error(
                            "You can only reference documents once they"
                            " have been saved to the database"
                        )
                    collection = v._get_collection_name()
                    value_dict[k] = DBRef(collection, v.pk)
                elif hasattr(v, "to_python"):
                    value_dict[k] = v.to_python()
                else:
                    value_dict[k] = self.to_python(v)

        if is_list:  # Convert back to a list
            return [
                v for _, v in sorted(value_dict.items(), key=operator.itemgetter(0))
            ]
        return value_dict

    def to_mongo(self, value, use_db_field=True, fields=None):
        """Convert a Python type to a MongoDB-compatible type."""
        Document = _import_class("Document")
        EmbeddedDocument = _import_class("EmbeddedDocument")
        GenericReferenceField = _import_class("GenericReferenceField")

        if isinstance(value, str):
            return value

        if hasattr(value, "to_mongo"):
            if isinstance(value, Document):
                return GenericReferenceField().to_mongo(value)
            cls = value.__class__
            val = value.to_mongo(use_db_field, fields)
            # If it's a document that is not inherited add _cls
            if isinstance(value, EmbeddedDocument):
                val["_cls"] = cls.__name__
            return val

        is_list = False
        if not hasattr(value, "items"):
            try:
                is_list = True
                value = {k: v for k, v in enumerate(value)}
            except TypeError:  # Not iterable return the value
                return value

        if self.field:
            value_dict = {
                key: self.field._to_mongo_safe_call(item, use_db_field, fields)
                for key, item in value.items()
            }
        else:
            value_dict = {}
            for k, v in value.items():
                if isinstance(v, Document):
                    # We need the id from the saved object to create the DBRef
                    if v.pk is None:
                        self.error(
                            "You can only reference documents once they"
                            " have been saved to the database"
                        )

                    # If its a document that is not inheritable it won't have
                    # any _cls data so make it a generic reference allows
                    # us to dereference
                    meta = getattr(v, "_meta", {})
                    allow_inheritance = meta.get("allow_inheritance")
                    if not allow_inheritance and not self.field:
                        value_dict[k] = GenericReferenceField().to_mongo(v)
                    else:
                        collection = v._get_collection_name()
                        value_dict[k] = DBRef(collection, v.pk)
                elif hasattr(v, "to_mongo"):
                    cls = v.__class__
                    val = v.to_mongo(use_db_field, fields)
                    # If it's a document that is not inherited add _cls
                    if isinstance(v, (Document, EmbeddedDocument)):
                        val["_cls"] = cls.__name__
                    value_dict[k] = val
                else:
                    value_dict[k] = self.to_mongo(v, use_db_field, fields)

        if is_list:  # Convert back to a list
            return [
                v for _, v in sorted(value_dict.items(), key=operator.itemgetter(0))
            ]
        return value_dict

    def validate(self, value):
        """If field is provided ensure the value is valid."""
        errors = {}
        if self.field:
            if hasattr(value, "items"):
                sequence = value.items()
            else:
                sequence = enumerate(value)
            for k, v in sequence:
                try:
                    self.field._validate(v)
                except ValidationError as error:
                    errors[k] = error.errors or error
                except (ValueError, AssertionError) as error:
                    errors[k] = error

            if errors:
                field_class = self.field.__class__.__name__
                self.error(f"Invalid {field_class} item ({value})", errors=errors)
        # Don't allow empty values if required
        if self.required and not value:
            self.error("Field is required and cannot be empty")

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def lookup_member(self, member_name):
        if self.field:
            return self.field.lookup_member(member_name)
        return None

    def _set_owner_document(self, owner_document):
        if self.field:
            self.field.owner_document = owner_document
        self._owner_document = owner_document


class ObjectIdField(BaseField):
    """A field wrapper around MongoDB's ObjectIds."""

    def to_python(self, value):
        try:
            if not isinstance(value, ObjectId):
                value = ObjectId(value)
        except Exception:
            pass
        return value

    def to_mongo(self, value):
        if not isinstance(value, ObjectId):
            try:
                return ObjectId(str(value))
            except Exception as e:
                self.error(str(e))
        return value

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def validate(self, value):
        try:
            ObjectId(str(value))
        except Exception:
            self.error("Invalid ObjectID")


class GeoJsonBaseField(BaseField):
    """A geo json field storing a geojson style object."""

    _geo_index = pymongo.GEOSPHERE
    _type = "GeoBase"

    def __init__(self, auto_index=True, *args, **kwargs):
        """
        :param bool auto_index: Automatically create a '2dsphere' index.\
            Defaults to `True`.
        """
        self._name = "%sField" % self._type
        if not auto_index:
            self._geo_index = False
        super().__init__(*args, **kwargs)

    def validate(self, value):
        """Validate the GeoJson object based on its type."""
        if isinstance(value, dict):
            if set(value.keys()) == {"type", "coordinates"}:
                if value["type"] != self._type:
                    self.error(f'{self._name} type must be "{self._type}"')
                return self.validate(value["coordinates"])
            else:
                self.error(
                    "%s can only accept a valid GeoJson dictionary"
                    " or lists of (x, y)" % self._name
                )
                return
        elif not isinstance(value, (list, tuple)):
            self.error("%s can only accept lists of [x, y]" % self._name)
            return

        validate = getattr(self, "_validate_%s" % self._type.lower())
        error = validate(value)
        if error:
            self.error(error)

    def _validate_polygon(self, value, top_level=True):
        if not isinstance(value, (list, tuple)):
            return "Polygons must contain list of linestrings"

        # Quick and dirty validator
        try:
            value[0][0][0]
        except (TypeError, IndexError):
            return "Invalid Polygon must contain at least one valid linestring"

        errors = []
        for val in value:
            error = self._validate_linestring(val, False)
            if not error and val[0] != val[-1]:
                error = "LineStrings must start and end at the same point"
            if error and error not in errors:
                errors.append(error)
        if errors:
            if top_level:
                return "Invalid Polygon:\n%s" % ", ".join(errors)
            else:
                return "%s" % ", ".join(errors)

    def _validate_linestring(self, value, top_level=True):
        """Validate a linestring."""
        if not isinstance(value, (list, tuple)):
            return "LineStrings must contain list of coordinate pairs"

        # Quick and dirty validator
        try:
            value[0][0]
        except (TypeError, IndexError):
            return "Invalid LineString must contain at least one valid point"

        errors = []
        for val in value:
            error = self._validate_point(val)
            if error and error not in errors:
                errors.append(error)
        if errors:
            if top_level:
                return "Invalid LineString:\n%s" % ", ".join(errors)
            else:
                return "%s" % ", ".join(errors)

    def _validate_point(self, value):
        """Validate each set of coords"""
        if not isinstance(value, (list, tuple)):
            return "Points must be a list of coordinate pairs"
        elif not len(value) == 2:
            return "Value (%s) must be a two-dimensional point" % repr(value)
        elif not isinstance(value[0], (float, int)) or not isinstance(
            value[1], (float, int)
        ):
            return "Both values (%s) in point must be float or int" % repr(value)

    def _validate_multipoint(self, value):
        if not isinstance(value, (list, tuple)):
            return "MultiPoint must be a list of Point"

        # Quick and dirty validator
        try:
            value[0][0]
        except (TypeError, IndexError):
            return "Invalid MultiPoint must contain at least one valid point"

        errors = []
        for point in value:
            error = self._validate_point(point)
            if error and error not in errors:
                errors.append(error)

        if errors:
            return "%s" % ", ".join(errors)

    def _validate_multilinestring(self, value, top_level=True):
        if not isinstance(value, (list, tuple)):
            return "MultiLineString must be a list of LineString"

        # Quick and dirty validator
        try:
            value[0][0][0]
        except (TypeError, IndexError):
            return "Invalid MultiLineString must contain at least one valid linestring"

        errors = []
        for linestring in value:
            error = self._validate_linestring(linestring, False)
            if error and error not in errors:
                errors.append(error)

        if errors:
            if top_level:
                return "Invalid MultiLineString:\n%s" % ", ".join(errors)
            else:
                return "%s" % ", ".join(errors)

    def _validate_multipolygon(self, value):
        if not isinstance(value, (list, tuple)):
            return "MultiPolygon must be a list of Polygon"

        # Quick and dirty validator
        try:
            value[0][0][0][0]
        except (TypeError, IndexError):
            return "Invalid MultiPolygon must contain at least one valid Polygon"

        errors = []
        for polygon in value:
            error = self._validate_polygon(polygon, False)
            if error and error not in errors:
                errors.append(error)

        if errors:
            return "Invalid MultiPolygon:\n%s" % ", ".join(errors)

    def to_mongo(self, value):
        if isinstance(value, dict):
            return value
        return SON([("type", self._type), ("coordinates", value)])
