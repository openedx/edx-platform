import itertools
import warnings

from mongoengine.base.common import _document_registry
from mongoengine.base.fields import (
    BaseField,
    ComplexBaseField,
    ObjectIdField,
)
from mongoengine.common import _import_class
from mongoengine.errors import InvalidDocumentError
from mongoengine.queryset import (
    DO_NOTHING,
    DoesNotExist,
    MultipleObjectsReturned,
    QuerySetManager,
)

__all__ = ("DocumentMetaclass", "TopLevelDocumentMetaclass")


class DocumentMetaclass(type):
    """Metaclass for all documents."""

    # TODO lower complexity of this method
    def __new__(mcs, name, bases, attrs):
        flattened_bases = mcs._get_bases(bases)
        super_new = super().__new__

        # If a base class just call super
        metaclass = attrs.get("my_metaclass")
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(mcs, name, bases, attrs)

        attrs["_is_document"] = attrs.get("_is_document", False)
        attrs["_cached_reference_fields"] = []

        # EmbeddedDocuments could have meta data for inheritance
        if "meta" in attrs:
            attrs["_meta"] = attrs.pop("meta")

        # EmbeddedDocuments should inherit meta data
        if "_meta" not in attrs:
            meta = MetaDict()
            for base in flattened_bases[::-1]:
                # Add any mixin metadata from plain objects
                if hasattr(base, "meta"):
                    meta.merge(base.meta)
                elif hasattr(base, "_meta"):
                    meta.merge(base._meta)
            attrs["_meta"] = meta
            attrs["_meta"][
                "abstract"
            ] = False  # 789: EmbeddedDocument shouldn't inherit abstract

        # If allow_inheritance is True, add a "_cls" string field to the attrs
        if attrs["_meta"].get("allow_inheritance"):
            StringField = _import_class("StringField")
            attrs["_cls"] = StringField()

        # Handle document Fields

        # Merge all fields from subclasses
        doc_fields = {}
        for base in flattened_bases[::-1]:
            if hasattr(base, "_fields"):
                doc_fields.update(base._fields)

            # Standard object mixin - merge in any Fields
            if not hasattr(base, "_meta"):
                base_fields = {}
                for attr_name, attr_value in base.__dict__.items():
                    if not isinstance(attr_value, BaseField):
                        continue
                    attr_value.name = attr_name
                    if not attr_value.db_field:
                        attr_value.db_field = attr_name
                    base_fields[attr_name] = attr_value

                doc_fields.update(base_fields)

        # Discover any document fields
        field_names = {}
        for attr_name, attr_value in attrs.items():
            if not isinstance(attr_value, BaseField):
                continue
            attr_value.name = attr_name
            if not attr_value.db_field:
                attr_value.db_field = attr_name
            doc_fields[attr_name] = attr_value

            # Count names to ensure no db_field redefinitions
            field_names[attr_value.db_field] = (
                field_names.get(attr_value.db_field, 0) + 1
            )

        # Ensure no duplicate db_fields
        duplicate_db_fields = [k for k, v in field_names.items() if v > 1]
        if duplicate_db_fields:
            msg = "Multiple db_fields defined for: %s " % ", ".join(duplicate_db_fields)
            raise InvalidDocumentError(msg)

        # Set _fields and db_field maps
        attrs["_fields"] = doc_fields
        attrs["_db_field_map"] = {
            k: getattr(v, "db_field", k) for k, v in doc_fields.items()
        }
        attrs["_reverse_db_field_map"] = {
            v: k for k, v in attrs["_db_field_map"].items()
        }

        attrs["_fields_ordered"] = tuple(
            i[1]
            for i in sorted((v.creation_counter, v.name) for v in doc_fields.values())
        )

        #
        # Set document hierarchy
        #
        superclasses = ()
        class_name = [name]
        for base in flattened_bases:
            if not getattr(base, "_is_base_cls", True) and not getattr(
                base, "_meta", {}
            ).get("abstract", True):
                # Collate hierarchy for _cls and _subclasses
                class_name.append(base.__name__)

            if hasattr(base, "_meta"):
                # Warn if allow_inheritance isn't set and prevent
                # inheritance of classes where inheritance is set to False
                allow_inheritance = base._meta.get("allow_inheritance")
                if not allow_inheritance and not base._meta.get("abstract"):
                    raise ValueError(
                        "Document %s may not be subclassed. "
                        'To enable inheritance, use the "allow_inheritance" meta attribute.'
                        % base.__name__
                    )

        # Get superclasses from last base superclass
        document_bases = [b for b in flattened_bases if hasattr(b, "_class_name")]
        if document_bases:
            superclasses = document_bases[0]._superclasses
            superclasses += (document_bases[0]._class_name,)

        _cls = ".".join(reversed(class_name))
        attrs["_class_name"] = _cls
        attrs["_superclasses"] = superclasses
        attrs["_subclasses"] = (_cls,)
        attrs["_types"] = attrs["_subclasses"]  # TODO depreciate _types

        # Create the new_class
        new_class = super_new(mcs, name, bases, attrs)

        # Set _subclasses
        for base in document_bases:
            if _cls not in base._subclasses:
                base._subclasses += (_cls,)
            base._types = base._subclasses  # TODO depreciate _types

        (
            Document,
            EmbeddedDocument,
            DictField,
            CachedReferenceField,
        ) = mcs._import_classes()

        if issubclass(new_class, Document):
            new_class._collection = None

        # Add class to the _document_registry
        _document_registry[new_class._class_name] = new_class

        # Handle delete rules
        for field in new_class._fields.values():
            f = field
            if f.owner_document is None:
                f.owner_document = new_class
            delete_rule = getattr(f, "reverse_delete_rule", DO_NOTHING)
            if isinstance(f, CachedReferenceField):

                if issubclass(new_class, EmbeddedDocument):
                    raise InvalidDocumentError(
                        "CachedReferenceFields is not allowed in EmbeddedDocuments"
                    )

                if f.auto_sync:
                    f.start_listener()

                f.document_type._cached_reference_fields.append(f)

            if isinstance(f, ComplexBaseField) and hasattr(f, "field"):
                delete_rule = getattr(f.field, "reverse_delete_rule", DO_NOTHING)
                if isinstance(f, DictField) and delete_rule != DO_NOTHING:
                    msg = (
                        "Reverse delete rules are not supported "
                        "for %s (field: %s)" % (field.__class__.__name__, field.name)
                    )
                    raise InvalidDocumentError(msg)

                f = field.field

            if delete_rule != DO_NOTHING:
                if issubclass(new_class, EmbeddedDocument):
                    msg = (
                        "Reverse delete rules are not supported for "
                        "EmbeddedDocuments (field: %s)" % field.name
                    )
                    raise InvalidDocumentError(msg)
                f.document_type.register_delete_rule(new_class, field.name, delete_rule)

            if (
                field.name
                and hasattr(Document, field.name)
                and EmbeddedDocument not in new_class.mro()
            ):
                msg = "%s is a document method and not a valid field name" % field.name
                raise InvalidDocumentError(msg)

        return new_class

    @classmethod
    def _get_bases(mcs, bases):
        if isinstance(bases, BasesTuple):
            return bases
        seen = []
        bases = mcs.__get_bases(bases)
        unique_bases = (b for b in bases if not (b in seen or seen.append(b)))
        return BasesTuple(unique_bases)

    @classmethod
    def __get_bases(mcs, bases):
        for base in bases:
            if base is object:
                continue
            yield base
            yield from mcs.__get_bases(base.__bases__)

    @classmethod
    def _import_classes(mcs):
        Document = _import_class("Document")
        EmbeddedDocument = _import_class("EmbeddedDocument")
        DictField = _import_class("DictField")
        CachedReferenceField = _import_class("CachedReferenceField")
        return Document, EmbeddedDocument, DictField, CachedReferenceField


class TopLevelDocumentMetaclass(DocumentMetaclass):
    """Metaclass for top-level documents (i.e. documents that have their own
    collection in the database.
    """

    def __new__(mcs, name, bases, attrs):
        flattened_bases = mcs._get_bases(bases)
        super_new = super().__new__

        # Set default _meta data if base class, otherwise get user defined meta
        if attrs.get("my_metaclass") == TopLevelDocumentMetaclass:
            # defaults
            attrs["_meta"] = {
                "abstract": True,
                "max_documents": None,
                "max_size": None,
                "ordering": [],  # default ordering applied at runtime
                "indexes": [],  # indexes to be ensured at runtime
                "id_field": None,
                "index_background": False,
                "index_opts": None,
                "delete_rules": None,
                # allow_inheritance can be True, False, and None. True means
                # "allow inheritance", False means "don't allow inheritance",
                # None means "do whatever your parent does, or don't allow
                # inheritance if you're a top-level class".
                "allow_inheritance": None,
            }
            attrs["_is_base_cls"] = True
            attrs["_meta"].update(attrs.get("meta", {}))
        else:
            attrs["_meta"] = attrs.get("meta", {})
            # Explicitly set abstract to false unless set
            attrs["_meta"]["abstract"] = attrs["_meta"].get("abstract", False)
            attrs["_is_base_cls"] = False

        # Set flag marking as document class - as opposed to an object mixin
        attrs["_is_document"] = True

        # Ensure queryset_class is inherited
        if "objects" in attrs:
            manager = attrs["objects"]
            if hasattr(manager, "queryset_class"):
                attrs["_meta"]["queryset_class"] = manager.queryset_class

        # Clean up top level meta
        if "meta" in attrs:
            del attrs["meta"]

        # Find the parent document class
        parent_doc_cls = [
            b for b in flattened_bases if b.__class__ == TopLevelDocumentMetaclass
        ]
        parent_doc_cls = None if not parent_doc_cls else parent_doc_cls[0]

        # Prevent classes setting collection different to their parents
        # If parent wasn't an abstract class
        if (
            parent_doc_cls
            and "collection" in attrs.get("_meta", {})
            and not parent_doc_cls._meta.get("abstract", True)
        ):
            msg = "Trying to set a collection on a subclass (%s)" % name
            warnings.warn(msg, SyntaxWarning)
            del attrs["_meta"]["collection"]

        # Ensure abstract documents have abstract bases
        if attrs.get("_is_base_cls") or attrs["_meta"].get("abstract"):
            if parent_doc_cls and not parent_doc_cls._meta.get("abstract", False):
                msg = "Abstract document cannot have non-abstract base"
                raise ValueError(msg)
            return super_new(mcs, name, bases, attrs)

        # Merge base class metas.
        # Uses a special MetaDict that handles various merging rules
        meta = MetaDict()
        for base in flattened_bases[::-1]:
            # Add any mixin metadata from plain objects
            if hasattr(base, "meta"):
                meta.merge(base.meta)
            elif hasattr(base, "_meta"):
                meta.merge(base._meta)

            # Set collection in the meta if its callable
            if getattr(base, "_is_document", False) and not base._meta.get("abstract"):
                collection = meta.get("collection", None)
                if callable(collection):
                    meta["collection"] = collection(base)

        meta.merge(attrs.get("_meta", {}))  # Top level meta

        # Only simple classes (i.e. direct subclasses of Document) may set
        # allow_inheritance to False. If the base Document allows inheritance,
        # none of its subclasses can override allow_inheritance to False.
        simple_class = all(
            b._meta.get("abstract") for b in flattened_bases if hasattr(b, "_meta")
        )
        if (
            not simple_class
            and meta["allow_inheritance"] is False
            and not meta["abstract"]
        ):
            raise ValueError(
                "Only direct subclasses of Document may set "
                '"allow_inheritance" to False'
            )

        # Set default collection name
        if "collection" not in meta:
            meta["collection"] = (
                "".join("_%s" % c if c.isupper() else c for c in name)
                .strip("_")
                .lower()
            )
        attrs["_meta"] = meta

        # Call super and get the new class
        new_class = super_new(mcs, name, bases, attrs)

        meta = new_class._meta

        # Set index specifications
        meta["index_specs"] = new_class._build_index_specs(meta["indexes"])

        # If collection is a callable - call it and set the value
        collection = meta.get("collection")
        if callable(collection):
            new_class._meta["collection"] = collection(new_class)

        # Provide a default queryset unless exists or one has been set
        if "objects" not in dir(new_class):
            new_class.objects = QuerySetManager()

        # Validate the fields and set primary key if needed
        for field_name, field in new_class._fields.items():
            if field.primary_key:
                # Ensure only one primary key is set
                current_pk = new_class._meta.get("id_field")
                if current_pk and current_pk != field_name:
                    raise ValueError("Cannot override primary key field")

                # Set primary key
                if not current_pk:
                    new_class._meta["id_field"] = field_name
                    new_class.id = field

        # If the document doesn't explicitly define a primary key field, create
        # one. Make it an ObjectIdField and give it a non-clashing name ("id"
        # by default, but can be different if that one's taken).
        if not new_class._meta.get("id_field"):
            id_name, id_db_name = mcs.get_auto_id_names(new_class)
            new_class._meta["id_field"] = id_name
            new_class._fields[id_name] = ObjectIdField(db_field=id_db_name)
            new_class._fields[id_name].name = id_name
            new_class.id = new_class._fields[id_name]
            new_class._db_field_map[id_name] = id_db_name
            new_class._reverse_db_field_map[id_db_name] = id_name

            # Prepend the ID field to _fields_ordered (so that it's *always*
            # the first field).
            new_class._fields_ordered = (id_name,) + new_class._fields_ordered

        # Merge in exceptions with parent hierarchy.
        exceptions_to_merge = (DoesNotExist, MultipleObjectsReturned)
        module = attrs.get("__module__")
        for exc in exceptions_to_merge:
            name = exc.__name__
            parents = tuple(
                getattr(base, name) for base in flattened_bases if hasattr(base, name)
            ) or (exc,)

            # Create a new exception and set it as an attribute on the new
            # class.
            exception = type(name, parents, {"__module__": module})
            setattr(new_class, name, exception)

        return new_class

    @classmethod
    def get_auto_id_names(mcs, new_class):
        """Find a name for the automatic ID field for the given new class.

        Return a two-element tuple where the first item is the field name (i.e.
        the attribute name on the object) and the second element is the DB
        field name (i.e. the name of the key stored in MongoDB).

        Defaults to ('id', '_id'), or generates a non-clashing name in the form
        of ('auto_id_X', '_auto_id_X') if the default name is already taken.
        """
        id_name, id_db_name = ("id", "_id")
        existing_fields = {field_name for field_name in new_class._fields}
        existing_db_fields = {v.db_field for v in new_class._fields.values()}
        if id_name not in existing_fields and id_db_name not in existing_db_fields:
            return id_name, id_db_name

        id_basename, id_db_basename, i = ("auto_id", "_auto_id", 0)
        for i in itertools.count():
            id_name = f"{id_basename}_{i}"
            id_db_name = f"{id_db_basename}_{i}"
            if id_name not in existing_fields and id_db_name not in existing_db_fields:
                return id_name, id_db_name


class MetaDict(dict):
    """Custom dictionary for meta classes.
    Handles the merging of set indexes
    """

    _merge_options = ("indexes",)

    def merge(self, new_options):
        for k, v in new_options.items():
            if k in self._merge_options:
                self[k] = self.get(k, []) + v
            else:
                self[k] = v


class BasesTuple(tuple):
    """Special class to handle introspection of bases tuple in __new__"""

    pass
