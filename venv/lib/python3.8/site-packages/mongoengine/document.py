import re

import pymongo
from bson.dbref import DBRef
from pymongo.read_preferences import ReadPreference

from mongoengine import signals
from mongoengine.base import (
    BaseDict,
    BaseDocument,
    BaseList,
    DocumentMetaclass,
    EmbeddedDocumentList,
    TopLevelDocumentMetaclass,
    get_document,
)
from mongoengine.common import _import_class
from mongoengine.connection import DEFAULT_CONNECTION_NAME, get_db
from mongoengine.context_managers import (
    set_write_concern,
    switch_collection,
    switch_db,
)
from mongoengine.errors import (
    InvalidDocumentError,
    InvalidQueryError,
    SaveConditionError,
)
from mongoengine.pymongo_support import list_collection_names
from mongoengine.queryset import (
    NotUniqueError,
    OperationError,
    QuerySet,
    transform,
)

__all__ = (
    "Document",
    "EmbeddedDocument",
    "DynamicDocument",
    "DynamicEmbeddedDocument",
    "OperationError",
    "InvalidCollectionError",
    "NotUniqueError",
    "MapReduceDocument",
)


def includes_cls(fields):
    """Helper function used for ensuring and comparing indexes."""
    first_field = None
    if len(fields):
        if isinstance(fields[0], str):
            first_field = fields[0]
        elif isinstance(fields[0], (list, tuple)) and len(fields[0]):
            first_field = fields[0][0]
    return first_field == "_cls"


class InvalidCollectionError(Exception):
    pass


class EmbeddedDocument(BaseDocument, metaclass=DocumentMetaclass):
    r"""A :class:`~mongoengine.Document` that isn't stored in its own
    collection.  :class:`~mongoengine.EmbeddedDocument`\ s should be used as
    fields on :class:`~mongoengine.Document`\ s through the
    :class:`~mongoengine.EmbeddedDocumentField` field type.

    A :class:`~mongoengine.EmbeddedDocument` subclass may be itself subclassed,
    to create a specialised version of the embedded document that will be
    stored in the same collection. To facilitate this behaviour a `_cls`
    field is added to documents (hidden though the MongoEngine interface).
    To enable this behaviour set :attr:`allow_inheritance` to ``True`` in the
    :attr:`meta` dictionary.
    """

    __slots__ = ("_instance",)

    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = DocumentMetaclass

    # A generic embedded document doesn't have any immutable properties
    # that describe it uniquely, hence it shouldn't be hashable. You can
    # define your own __hash__ method on a subclass if you need your
    # embedded documents to be hashable.
    __hash__ = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = None
        self._changed_fields = []

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getstate__(self):
        data = super().__getstate__()
        data["_instance"] = None
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self._instance = state["_instance"]

    def to_mongo(self, *args, **kwargs):
        data = super().to_mongo(*args, **kwargs)

        # remove _id from the SON if it's in it and it's None
        if "_id" in data and data["_id"] is None:
            del data["_id"]

        return data


class Document(BaseDocument, metaclass=TopLevelDocumentMetaclass):
    """The base class used for defining the structure and properties of
    collections of documents stored in MongoDB. Inherit from this class, and
    add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~mongoengine.Document` subclass.

    By default, the MongoDB collection used to store documents created using a
    :class:`~mongoengine.Document` subclass will be the name of the subclass
    converted to snake_case. A different collection may be specified by
    providing :attr:`collection` to the :attr:`meta` dictionary in the class
    definition.

    A :class:`~mongoengine.Document` subclass may be itself subclassed, to
    create a specialised version of the document that will be stored in the
    same collection. To facilitate this behaviour a `_cls`
    field is added to documents (hidden though the MongoEngine interface).
    To enable this behaviour set :attr:`allow_inheritance` to ``True`` in the
    :attr:`meta` dictionary.

    A :class:`~mongoengine.Document` may use a **Capped Collection** by
    specifying :attr:`max_documents` and :attr:`max_size` in the :attr:`meta`
    dictionary. :attr:`max_documents` is the maximum number of documents that
    is allowed to be stored in the collection, and :attr:`max_size` is the
    maximum size of the collection in bytes. :attr:`max_size` is rounded up
    to the next multiple of 256 by MongoDB internally and mongoengine before.
    Use also a multiple of 256 to avoid confusions.  If :attr:`max_size` is not
    specified and :attr:`max_documents` is, :attr:`max_size` defaults to
    10485760 bytes (10MB).

    Indexes may be created by specifying :attr:`indexes` in the :attr:`meta`
    dictionary. The value should be a list of field names or tuples of field
    names. Index direction may be specified by prefixing the field names with
    a **+** or **-** sign.

    Automatic index creation can be disabled by specifying
    :attr:`auto_create_index` in the :attr:`meta` dictionary. If this is set to
    False then indexes will not be created by MongoEngine.  This is useful in
    production systems where index creation is performed as part of a
    deployment system.

    By default, _cls will be added to the start of every index (that
    doesn't contain a list) if allow_inheritance is True. This can be
    disabled by either setting cls to False on the specific index or
    by setting index_cls to False on the meta dictionary for the document.

    By default, any extra attribute existing in stored data but not declared
    in your model will raise a :class:`~mongoengine.FieldDoesNotExist` error.
    This can be disabled by setting :attr:`strict` to ``False``
    in the :attr:`meta` dictionary.
    """

    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = TopLevelDocumentMetaclass

    __slots__ = ("__objects",)

    @property
    def pk(self):
        """Get the primary key."""
        if "id_field" not in self._meta:
            return None
        return getattr(self, self._meta["id_field"])

    @pk.setter
    def pk(self, value):
        """Set the primary key."""
        return setattr(self, self._meta["id_field"], value)

    def __hash__(self):
        """Return the hash based on the PK of this document. If it's new
        and doesn't have a PK yet, return the default object hash instead.
        """
        if self.pk is None:
            return super(BaseDocument, self).__hash__()

        return hash(self.pk)

    @classmethod
    def _get_db(cls):
        """Some Model using other db_alias"""
        return get_db(cls._meta.get("db_alias", DEFAULT_CONNECTION_NAME))

    @classmethod
    def _disconnect(cls):
        """Detach the Document class from the (cached) database collection"""
        cls._collection = None

    @classmethod
    def _get_collection(cls):
        """Return the PyMongo collection corresponding to this document.

        Upon first call, this method:
        1. Initializes a :class:`~pymongo.collection.Collection` corresponding
           to this document.
        2. Creates indexes defined in this document's :attr:`meta` dictionary.
           This happens only if `auto_create_index` is True.
        """
        if not hasattr(cls, "_collection") or cls._collection is None:
            # Get the collection, either capped or regular.
            if cls._meta.get("max_size") or cls._meta.get("max_documents"):
                cls._collection = cls._get_capped_collection()
            else:
                db = cls._get_db()
                collection_name = cls._get_collection_name()
                cls._collection = db[collection_name]

            # Ensure indexes on the collection unless auto_create_index was
            # set to False.
            # Also there is no need to ensure indexes on slave.
            db = cls._get_db()
            if cls._meta.get("auto_create_index", True) and db.client.is_primary:
                cls.ensure_indexes()

        return cls._collection

    @classmethod
    def _get_capped_collection(cls):
        """Create a new or get an existing capped PyMongo collection."""
        db = cls._get_db()
        collection_name = cls._get_collection_name()

        # Get max document limit and max byte size from meta.
        max_size = cls._meta.get("max_size") or 10 * 2**20  # 10MB default
        max_documents = cls._meta.get("max_documents")

        # MongoDB will automatically raise the size to make it a multiple of
        # 256 bytes. We raise it here ourselves to be able to reliably compare
        # the options below.
        if max_size % 256:
            max_size = (max_size // 256 + 1) * 256

        # If the collection already exists and has different options
        # (i.e. isn't capped or has different max/size), raise an error.
        if collection_name in list_collection_names(
            db, include_system_collections=True
        ):
            collection = db[collection_name]
            options = collection.options()
            if options.get("max") != max_documents or options.get("size") != max_size:
                raise InvalidCollectionError(
                    'Cannot create collection "{}" as a capped '
                    "collection as it already exists".format(cls._collection)
                )

            return collection

        # Create a new capped collection.
        opts = {"capped": True, "size": max_size}
        if max_documents:
            opts["max"] = max_documents

        return db.create_collection(collection_name, **opts)

    def to_mongo(self, *args, **kwargs):
        data = super().to_mongo(*args, **kwargs)

        # If '_id' is None, try and set it from self._data. If that
        # doesn't exist either, remove '_id' from the SON completely.
        if data["_id"] is None:
            if self._data.get("id") is None:
                del data["_id"]
            else:
                data["_id"] = self._data["id"]

        return data

    def modify(self, query=None, **update):
        """Perform an atomic update of the document in the database and reload
        the document object using updated version.

        Returns True if the document has been updated or False if the document
        in the database doesn't match the query.

        .. note:: All unsaved changes that have been made to the document are
            rejected if the method returns True.

        :param query: the update will be performed only if the document in the
            database matches the query
        :param update: Django-style update keyword arguments
        """
        if query is None:
            query = {}

        if self.pk is None:
            raise InvalidDocumentError("The document does not have a primary key.")

        id_field = self._meta["id_field"]
        query = query.copy() if isinstance(query, dict) else query.to_query(self)

        if id_field not in query:
            query[id_field] = self.pk
        elif query[id_field] != self.pk:
            raise InvalidQueryError(
                "Invalid document modify query: it must modify only this document."
            )

        # Need to add shard key to query, or you get an error
        query.update(self._object_key)

        updated = self._qs(**query).modify(new=True, **update)
        if updated is None:
            return False

        for field in self._fields_ordered:
            setattr(self, field, self._reload(field, updated[field]))

        self._changed_fields = updated._changed_fields
        self._created = False

        return True

    def save(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        cascade=None,
        cascade_kwargs=None,
        _refs=None,
        save_condition=None,
        signal_kwargs=None,
        **kwargs,
    ):
        """Save the :class:`~mongoengine.Document` to the database. If the
        document already exists, it will be updated, otherwise it will be
        created. Returns the saved object instance.

        :param force_insert: only try to create a new document, don't allow
            updates of existing documents.
        :param validate: validates the document; set to ``False`` to skip.
        :param clean: call the document clean method, requires `validate` to be
            True.
        :param write_concern: Extra keyword arguments are passed down to
            :meth:`~pymongo.collection.Collection.save` OR
            :meth:`~pymongo.collection.Collection.insert`
            which will be used as options for the resultant
            ``getLastError`` command.  For example,
            ``save(..., write_concern={w: 2, fsync: True}, ...)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        :param cascade: Sets the flag for cascading saves.  You can set a
            default by setting "cascade" in the document __meta__
        :param cascade_kwargs: (optional) kwargs dictionary to be passed throw
            to cascading saves.  Implies ``cascade=True``.
        :param _refs: A list of processed references used in cascading saves
        :param save_condition: only perform save if matching record in db
            satisfies condition(s) (e.g. version number).
            Raises :class:`OperationError` if the conditions are not satisfied
        :param signal_kwargs: (optional) kwargs dictionary to be passed to
            the signal calls.

        .. versionchanged:: 0.5
            In existing documents it only saves changed fields using
            set / unset.  Saves are cascaded and any
            :class:`~bson.dbref.DBRef` objects that have changes are
            saved as well.
        .. versionchanged:: 0.6
            Added cascading saves
        .. versionchanged:: 0.8
            Cascade saves are optional and default to False.  If you want
            fine grain control then you can turn off using document
            meta['cascade'] = True.  Also you can pass different kwargs to
            the cascade save using cascade_kwargs which overwrites the
            existing kwargs with custom values.
        """
        signal_kwargs = signal_kwargs or {}

        if self._meta.get("abstract"):
            raise InvalidDocumentError("Cannot save an abstract document.")

        signals.pre_save.send(self.__class__, document=self, **signal_kwargs)

        if validate:
            self.validate(clean=clean)

        if write_concern is None:
            write_concern = {}

        doc_id = self.to_mongo(fields=[self._meta["id_field"]])
        created = "_id" not in doc_id or self._created or force_insert

        signals.pre_save_post_validation.send(
            self.__class__, document=self, created=created, **signal_kwargs
        )
        # it might be refreshed by the pre_save_post_validation hook, e.g., for etag generation
        doc = self.to_mongo()

        if self._meta.get("auto_create_index", True):
            self.ensure_indexes()

        try:
            # Save a new document or update an existing one
            if created:
                object_id = self._save_create(doc, force_insert, write_concern)
            else:
                object_id, created = self._save_update(
                    doc, save_condition, write_concern
                )

            if cascade is None:
                cascade = self._meta.get("cascade", False) or cascade_kwargs is not None

            if cascade:
                kwargs = {
                    "force_insert": force_insert,
                    "validate": validate,
                    "write_concern": write_concern,
                    "cascade": cascade,
                }
                if cascade_kwargs:  # Allow granular control over cascades
                    kwargs.update(cascade_kwargs)
                kwargs["_refs"] = _refs
                self.cascade_save(**kwargs)

        except pymongo.errors.DuplicateKeyError as err:
            message = "Tried to save duplicate unique keys (%s)"
            raise NotUniqueError(message % err)
        except pymongo.errors.OperationFailure as err:
            message = "Could not save document (%s)"
            if re.match("^E1100[01] duplicate key", str(err)):
                # E11000 - duplicate key error index
                # E11001 - duplicate key on update
                message = "Tried to save duplicate unique keys (%s)"
                raise NotUniqueError(message % err)
            raise OperationError(message % err)

        # Make sure we store the PK on this document now that it's saved
        id_field = self._meta["id_field"]
        if created or id_field not in self._meta.get("shard_key", []):
            self[id_field] = self._fields[id_field].to_python(object_id)

        signals.post_save.send(
            self.__class__, document=self, created=created, **signal_kwargs
        )

        self._clear_changed_fields()
        self._created = False

        return self

    def _save_create(self, doc, force_insert, write_concern):
        """Save a new document.

        Helper method, should only be used inside save().
        """
        collection = self._get_collection()
        with set_write_concern(collection, write_concern) as wc_collection:
            if force_insert:
                return wc_collection.insert_one(doc).inserted_id
            # insert_one will provoke UniqueError alongside save does not
            # therefore, it need to catch and call replace_one.
            if "_id" in doc:
                select_dict = {"_id": doc["_id"]}
                select_dict = self._integrate_shard_key(doc, select_dict)
                raw_object = wc_collection.find_one_and_replace(select_dict, doc)
                if raw_object:
                    return doc["_id"]

            object_id = wc_collection.insert_one(doc).inserted_id

        return object_id

    def _get_update_doc(self):
        """Return a dict containing all the $set and $unset operations
        that should be sent to MongoDB based on the changes made to this
        Document.
        """
        updates, removals = self._delta()

        update_doc = {}
        if updates:
            update_doc["$set"] = updates
        if removals:
            update_doc["$unset"] = removals

        return update_doc

    def _integrate_shard_key(self, doc, select_dict):
        """Integrates the collection's shard key to the `select_dict`, which will be used for the query.
        The value from the shard key is taken from the `doc` and finally the select_dict is returned.
        """

        # Need to add shard key to query, or you get an error
        shard_key = self._meta.get("shard_key", tuple())
        for k in shard_key:
            path = self._lookup_field(k.split("."))
            actual_key = [p.db_field for p in path]
            val = doc
            for ak in actual_key:
                val = val[ak]
            select_dict[".".join(actual_key)] = val

        return select_dict

    def _save_update(self, doc, save_condition, write_concern):
        """Update an existing document.

        Helper method, should only be used inside save().
        """
        collection = self._get_collection()
        object_id = doc["_id"]
        created = False

        select_dict = {}
        if save_condition is not None:
            select_dict = transform.query(self.__class__, **save_condition)

        select_dict["_id"] = object_id

        select_dict = self._integrate_shard_key(doc, select_dict)

        update_doc = self._get_update_doc()
        if update_doc:
            upsert = save_condition is None
            with set_write_concern(collection, write_concern) as wc_collection:
                last_error = wc_collection.update_one(
                    select_dict, update_doc, upsert=upsert
                ).raw_result
            if not upsert and last_error["n"] == 0:
                raise SaveConditionError(
                    "Race condition preventing document update detected"
                )
            if last_error is not None:
                updated_existing = last_error.get("updatedExisting")
                if updated_existing is False:
                    created = True
                    # !!! This is bad, means we accidentally created a new,
                    # potentially corrupted document. See
                    # https://github.com/MongoEngine/mongoengine/issues/564

        return object_id, created

    def cascade_save(self, **kwargs):
        """Recursively save any references and generic references on the
        document.
        """
        _refs = kwargs.get("_refs") or []

        ReferenceField = _import_class("ReferenceField")
        GenericReferenceField = _import_class("GenericReferenceField")

        for name, cls in self._fields.items():
            if not isinstance(cls, (ReferenceField, GenericReferenceField)):
                continue

            ref = self._data.get(name)
            if not ref or isinstance(ref, DBRef):
                continue

            if not getattr(ref, "_changed_fields", True):
                continue

            ref_id = f"{ref.__class__.__name__},{str(ref._data)}"
            if ref and ref_id not in _refs:
                _refs.append(ref_id)
                kwargs["_refs"] = _refs
                ref.save(**kwargs)
                ref._changed_fields = []

    @property
    def _qs(self):
        """Return the default queryset corresponding to this document."""
        if not hasattr(self, "__objects"):
            queryset_class = self._meta.get("queryset_class", QuerySet)
            self.__objects = queryset_class(self.__class__, self._get_collection())
        return self.__objects

    @property
    def _object_key(self):
        """Return a query dict that can be used to fetch this document.

        Most of the time the dict is a simple PK lookup, but in case of
        a sharded collection with a compound shard key, it can contain a more
        complex query.

        Note that the dict returned by this method uses MongoEngine field
        names instead of PyMongo field names (e.g. "pk" instead of "_id",
        "some__nested__field" instead of "some.nested.field", etc.).
        """
        select_dict = {"pk": self.pk}
        shard_key = self.__class__._meta.get("shard_key", tuple())
        for k in shard_key:
            val = self
            field_parts = k.split(".")
            for part in field_parts:
                val = getattr(val, part)
            select_dict["__".join(field_parts)] = val
        return select_dict

    def update(self, **kwargs):
        """Performs an update on the :class:`~mongoengine.Document`
        A convenience wrapper to :meth:`~mongoengine.QuerySet.update`.

        Raises :class:`OperationError` if called on an object that has not yet
        been saved.
        """
        if self.pk is None:
            if kwargs.get("upsert", False):
                query = self.to_mongo()
                if "_cls" in query:
                    del query["_cls"]
                return self._qs.filter(**query).update_one(**kwargs)
            else:
                raise OperationError("attempt to update a document not yet saved")

        # Need to add shard key to query, or you get an error
        return self._qs.filter(**self._object_key).update_one(**kwargs)

    def delete(self, signal_kwargs=None, **write_concern):
        """Delete the :class:`~mongoengine.Document` from the database. This
        will only take effect if the document has been previously saved.

        :param signal_kwargs: (optional) kwargs dictionary to be passed to
            the signal calls.
        :param write_concern: Extra keyword arguments are passed down which
            will be used as options for the resultant ``getLastError`` command.
            For example, ``save(..., w: 2, fsync: True)`` will
            wait until at least two servers have recorded the write and
            will force an fsync on the primary server.
        """
        signal_kwargs = signal_kwargs or {}
        signals.pre_delete.send(self.__class__, document=self, **signal_kwargs)

        # Delete FileFields separately
        FileField = _import_class("FileField")
        for name, field in self._fields.items():
            if isinstance(field, FileField):
                getattr(self, name).delete()

        try:
            self._qs.filter(**self._object_key).delete(
                write_concern=write_concern, _from_doc_delete=True
            )
        except pymongo.errors.OperationFailure as err:
            message = "Could not delete document (%s)" % err.args
            raise OperationError(message)
        signals.post_delete.send(self.__class__, document=self, **signal_kwargs)

    def switch_db(self, db_alias, keep_created=True):
        """
        Temporarily switch the database for a document instance.

        Only really useful for archiving off data and calling `save()`::

            user = User.objects.get(id=user_id)
            user.switch_db('archive-db')
            user.save()

        :param str db_alias: The database alias to use for saving the document

        :param bool keep_created: keep self._created value after switching db, else is reset to True


        .. seealso::
            Use :class:`~mongoengine.context_managers.switch_collection`
            if you need to read from another collection
        """
        with switch_db(self.__class__, db_alias) as cls:
            collection = cls._get_collection()
            db = cls._get_db()
        self._get_collection = lambda: collection
        self._get_db = lambda: db
        self._collection = collection
        self._created = True if not keep_created else self._created
        self.__objects = self._qs
        self.__objects._collection_obj = collection
        return self

    def switch_collection(self, collection_name, keep_created=True):
        """
        Temporarily switch the collection for a document instance.

        Only really useful for archiving off data and calling `save()`::

            user = User.objects.get(id=user_id)
            user.switch_collection('old-users')
            user.save()

        :param str collection_name: The database alias to use for saving the
            document

        :param bool keep_created: keep self._created value after switching collection, else is reset to True


        .. seealso::
            Use :class:`~mongoengine.context_managers.switch_db`
            if you need to read from another database
        """
        with switch_collection(self.__class__, collection_name) as cls:
            collection = cls._get_collection()
        self._get_collection = lambda: collection
        self._collection = collection
        self._created = True if not keep_created else self._created
        self.__objects = self._qs
        self.__objects._collection_obj = collection
        return self

    def select_related(self, max_depth=1):
        """Handles dereferencing of :class:`~bson.dbref.DBRef` objects to
        a maximum depth in order to cut down the number queries to mongodb.
        """
        DeReference = _import_class("DeReference")
        DeReference()([self], max_depth + 1)
        return self

    def reload(self, *fields, **kwargs):
        """Reloads all attributes from the database.

        :param fields: (optional) args list of fields to reload
        :param max_depth: (optional) depth of dereferencing to follow
        """
        max_depth = 1
        if fields and isinstance(fields[0], int):
            max_depth = fields[0]
            fields = fields[1:]
        elif "max_depth" in kwargs:
            max_depth = kwargs["max_depth"]

        if self.pk is None:
            raise self.DoesNotExist("Document does not exist")

        obj = (
            self._qs.read_preference(ReadPreference.PRIMARY)
            .filter(**self._object_key)
            .only(*fields)
            .limit(1)
            .select_related(max_depth=max_depth)
        )

        if obj:
            obj = obj[0]
        else:
            raise self.DoesNotExist("Document does not exist")
        for field in obj._data:
            if not fields or field in fields:
                try:
                    setattr(self, field, self._reload(field, obj[field]))
                except (KeyError, AttributeError):
                    try:
                        # If field is a special field, e.g. items is stored as _reserved_items,
                        # a KeyError is thrown. So try to retrieve the field from _data
                        setattr(self, field, self._reload(field, obj._data.get(field)))
                    except KeyError:
                        # If field is removed from the database while the object
                        # is in memory, a reload would cause a KeyError
                        # i.e. obj.update(unset__field=1) followed by obj.reload()
                        delattr(self, field)

        self._changed_fields = (
            list(set(self._changed_fields) - set(fields))
            if fields
            else obj._changed_fields
        )
        self._created = False
        return self

    def _reload(self, key, value):
        """Used by :meth:`~mongoengine.Document.reload` to ensure the
        correct instance is linked to self.
        """
        if isinstance(value, BaseDict):
            value = [(k, self._reload(k, v)) for k, v in value.items()]
            value = BaseDict(value, self, key)
        elif isinstance(value, EmbeddedDocumentList):
            value = [self._reload(key, v) for v in value]
            value = EmbeddedDocumentList(value, self, key)
        elif isinstance(value, BaseList):
            value = [self._reload(key, v) for v in value]
            value = BaseList(value, self, key)
        elif isinstance(value, (EmbeddedDocument, DynamicEmbeddedDocument)):
            value._instance = None
            value._changed_fields = []
        return value

    def to_dbref(self):
        """Returns an instance of :class:`~bson.dbref.DBRef` useful in
        `__raw__` queries."""
        if self.pk is None:
            msg = "Only saved documents can have a valid dbref"
            raise OperationError(msg)
        return DBRef(self.__class__._get_collection_name(), self.pk)

    @classmethod
    def register_delete_rule(cls, document_cls, field_name, rule):
        """This method registers the delete rules to apply when removing this
        object.
        """
        classes = [
            get_document(class_name)
            for class_name in cls._subclasses
            if class_name != cls.__name__
        ] + [cls]
        documents = [
            get_document(class_name)
            for class_name in document_cls._subclasses
            if class_name != document_cls.__name__
        ] + [document_cls]

        for klass in classes:
            for document_cls in documents:
                delete_rules = klass._meta.get("delete_rules") or {}
                delete_rules[(document_cls, field_name)] = rule
                klass._meta["delete_rules"] = delete_rules

    @classmethod
    def drop_collection(cls):
        """Drops the entire collection associated with this
        :class:`~mongoengine.Document` type from the database.

        Raises :class:`OperationError` if the document has no collection set
        (i.g. if it is `abstract`)
        """
        coll_name = cls._get_collection_name()
        if not coll_name:
            raise OperationError(
                "Document %s has no collection defined (is it abstract ?)" % cls
            )
        cls._collection = None
        db = cls._get_db()
        db.drop_collection(coll_name)

    @classmethod
    def create_index(cls, keys, background=False, **kwargs):
        """Creates the given indexes if required.

        :param keys: a single index key or a list of index keys (to
            construct a multi-field index); keys may be prefixed with a **+**
            or a **-** to determine the index ordering
        :param background: Allows index creation in the background
        """
        index_spec = cls._build_index_spec(keys)
        index_spec = index_spec.copy()
        fields = index_spec.pop("fields")
        index_spec["background"] = background
        index_spec.update(kwargs)

        return cls._get_collection().create_index(fields, **index_spec)

    @classmethod
    def ensure_index(cls, key_or_list, background=False, **kwargs):
        """Ensure that the given indexes are in place. Deprecated in favour
        of create_index.

        :param key_or_list: a single index key or a list of index keys (to
            construct a multi-field index); keys may be prefixed with a **+**
            or a **-** to determine the index ordering
        :param background: Allows index creation in the background
        """
        return cls.create_index(key_or_list, background=background, **kwargs)

    @classmethod
    def ensure_indexes(cls):
        """Checks the document meta data and ensures all the indexes exist.

        Global defaults can be set in the meta - see :doc:`guide/defining-documents`

        By default, this will get called automatically upon first interaction with the
        Document collection (query, save, etc) so unless you disabled `auto_create_index`, you
        shouldn't have to call this manually.

        .. note:: You can disable automatic index creation by setting
                  `auto_create_index` to False in the documents meta data
        """
        background = cls._meta.get("index_background", False)
        index_opts = cls._meta.get("index_opts") or {}
        index_cls = cls._meta.get("index_cls", True)

        collection = cls._get_collection()

        # determine if an index which we are creating includes
        # _cls as its first field; if so, we can avoid creating
        # an extra index on _cls, as mongodb will use the existing
        # index to service queries against _cls
        cls_indexed = False

        # Ensure document-defined indexes are created
        if cls._meta["index_specs"]:
            index_spec = cls._meta["index_specs"]
            for spec in index_spec:
                spec = spec.copy()
                fields = spec.pop("fields")
                cls_indexed = cls_indexed or includes_cls(fields)
                opts = index_opts.copy()
                opts.update(spec)

                # we shouldn't pass 'cls' to the collection.ensureIndex options
                # because of https://jira.mongodb.org/browse/SERVER-769
                if "cls" in opts:
                    del opts["cls"]

                collection.create_index(fields, background=background, **opts)

        # If _cls is being used (for polymorphism), it needs an index,
        # only if another index doesn't begin with _cls
        if index_cls and not cls_indexed and cls._meta.get("allow_inheritance"):

            # we shouldn't pass 'cls' to the collection.ensureIndex options
            # because of https://jira.mongodb.org/browse/SERVER-769
            if "cls" in index_opts:
                del index_opts["cls"]

            collection.create_index("_cls", background=background, **index_opts)

    @classmethod
    def list_indexes(cls):
        """Lists all indexes that should be created for the Document collection.
        It includes all the indexes from super- and sub-classes.

        Note that it will only return the indexes' fields, not the indexes' options
        """
        if cls._meta.get("abstract"):
            return []

        # get all the base classes, subclasses and siblings
        classes = []

        def get_classes(cls):

            if cls not in classes and isinstance(cls, TopLevelDocumentMetaclass):
                classes.append(cls)

            for base_cls in cls.__bases__:
                if (
                    isinstance(base_cls, TopLevelDocumentMetaclass)
                    and base_cls != Document
                    and not base_cls._meta.get("abstract")
                    and base_cls._get_collection().full_name
                    == cls._get_collection().full_name
                    and base_cls not in classes
                ):
                    classes.append(base_cls)
                    get_classes(base_cls)
            for subclass in cls.__subclasses__():
                if (
                    isinstance(base_cls, TopLevelDocumentMetaclass)
                    and subclass._get_collection().full_name
                    == cls._get_collection().full_name
                    and subclass not in classes
                ):
                    classes.append(subclass)
                    get_classes(subclass)

        get_classes(cls)

        # get the indexes spec for all of the gathered classes
        def get_indexes_spec(cls):
            indexes = []

            if cls._meta["index_specs"]:
                index_spec = cls._meta["index_specs"]
                for spec in index_spec:
                    spec = spec.copy()
                    fields = spec.pop("fields")
                    indexes.append(fields)
            return indexes

        indexes = []
        for klass in classes:
            for index in get_indexes_spec(klass):
                if index not in indexes:
                    indexes.append(index)

        # finish up by appending { '_id': 1 } and { '_cls': 1 }, if needed
        if [("_id", 1)] not in indexes:
            indexes.append([("_id", 1)])
        if cls._meta.get("index_cls", True) and cls._meta.get("allow_inheritance"):
            indexes.append([("_cls", 1)])

        return indexes

    @classmethod
    def compare_indexes(cls):
        """Compares the indexes defined in MongoEngine with the ones
        existing in the database. Returns any missing/extra indexes.
        """

        required = cls.list_indexes()

        existing = []
        for info in cls._get_collection().index_information().values():
            if "_fts" in info["key"][0]:
                index_type = info["key"][0][1]
                text_index_fields = info.get("weights").keys()
                existing.append([(key, index_type) for key in text_index_fields])
            else:
                existing.append(info["key"])
        missing = [index for index in required if index not in existing]
        extra = [index for index in existing if index not in required]

        # if { _cls: 1 } is missing, make sure it's *really* necessary
        if [("_cls", 1)] in missing:
            cls_obsolete = False
            for index in existing:
                if includes_cls(index) and index not in extra:
                    cls_obsolete = True
                    break
            if cls_obsolete:
                missing.remove([("_cls", 1)])

        return {"missing": missing, "extra": extra}


class DynamicDocument(Document, metaclass=TopLevelDocumentMetaclass):
    """A Dynamic Document class allowing flexible, expandable and uncontrolled
    schemas.  As a :class:`~mongoengine.Document` subclass, acts in the same
    way as an ordinary document but has expanded style properties.  Any data
    passed or set against the :class:`~mongoengine.DynamicDocument` that is
    not a field is automatically converted into a
    :class:`~mongoengine.fields.DynamicField` and data can be attributed to that
    field.

    .. note::

        There is one caveat on Dynamic Documents: undeclared fields cannot start with `_`
    """

    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = TopLevelDocumentMetaclass

    _dynamic = True

    def __delattr__(self, *args, **kwargs):
        """Delete the attribute by setting to None and allowing _delta
        to unset it.
        """
        field_name = args[0]
        if field_name in self._dynamic_fields:
            setattr(self, field_name, None)
            self._dynamic_fields[field_name].null = False
        else:
            super().__delattr__(*args, **kwargs)


class DynamicEmbeddedDocument(EmbeddedDocument, metaclass=DocumentMetaclass):
    """A Dynamic Embedded Document class allowing flexible, expandable and
    uncontrolled schemas. See :class:`~mongoengine.DynamicDocument` for more
    information about dynamic documents.
    """

    # my_metaclass is defined so that metaclass can be queried in Python 2 & 3
    my_metaclass = DocumentMetaclass

    _dynamic = True

    def __delattr__(self, *args, **kwargs):
        """Delete the attribute by setting to None and allowing _delta
        to unset it.
        """
        field_name = args[0]
        if field_name in self._fields:
            default = self._fields[field_name].default
            if callable(default):
                default = default()
            setattr(self, field_name, default)
        else:
            setattr(self, field_name, None)


class MapReduceDocument:
    """A document returned from a map/reduce query.

    :param collection: An instance of :class:`~pymongo.Collection`
    :param key: Document/result key, often an instance of
                :class:`~bson.objectid.ObjectId`. If supplied as
                an ``ObjectId`` found in the given ``collection``,
                the object can be accessed via the ``object`` property.
    :param value: The result(s) for this key.
    """

    def __init__(self, document, collection, key, value):
        self._document = document
        self._collection = collection
        self.key = key
        self.value = value

    @property
    def object(self):
        """Lazy-load the object referenced by ``self.key``. ``self.key``
        should be the ``primary_key``.
        """
        id_field = self._document()._meta["id_field"]
        id_field_type = type(id_field)

        if not isinstance(self.key, id_field_type):
            try:
                self.key = id_field_type(self.key)
            except Exception:
                raise Exception("Could not cast key as %s" % id_field_type.__name__)

        if not hasattr(self, "_key_object"):
            self._key_object = self._document.objects.with_id(self.key)
            return self._key_object
        return self._key_object
