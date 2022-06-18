import weakref

from bson import DBRef

from mongoengine.common import _import_class
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned

__all__ = (
    "BaseDict",
    "StrictDict",
    "BaseList",
    "EmbeddedDocumentList",
    "LazyReference",
)


def mark_as_changed_wrapper(parent_method):
    """Decorator that ensures _mark_as_changed method gets called."""

    def wrapper(self, *args, **kwargs):
        # Can't use super() in the decorator.
        result = parent_method(self, *args, **kwargs)
        self._mark_as_changed()
        return result

    return wrapper


def mark_key_as_changed_wrapper(parent_method):
    """Decorator that ensures _mark_as_changed method gets called with the key argument"""

    def wrapper(self, key, *args, **kwargs):
        # Can't use super() in the decorator.
        result = parent_method(self, key, *args, **kwargs)
        self._mark_as_changed(key)
        return result

    return wrapper


class BaseDict(dict):
    """A special dict so we can watch any changes."""

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, dict_items, instance, name):
        BaseDocument = _import_class("BaseDocument")

        if isinstance(instance, BaseDocument):
            self._instance = weakref.proxy(instance)
        self._name = name
        super().__init__(dict_items)

    def get(self, key, default=None):
        # get does not use __getitem__ by default so we must override it as well
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        value = super().__getitem__(key)

        EmbeddedDocument = _import_class("EmbeddedDocument")
        if isinstance(value, EmbeddedDocument) and value._instance is None:
            value._instance = self._instance
        elif isinstance(value, dict) and not isinstance(value, BaseDict):
            value = BaseDict(value, None, f"{self._name}.{key}")
            super().__setitem__(key, value)
            value._instance = self._instance
        elif isinstance(value, list) and not isinstance(value, BaseList):
            value = BaseList(value, None, f"{self._name}.{key}")
            super().__setitem__(key, value)
            value._instance = self._instance
        return value

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    __setitem__ = mark_key_as_changed_wrapper(dict.__setitem__)
    __delattr__ = mark_key_as_changed_wrapper(dict.__delattr__)
    __delitem__ = mark_key_as_changed_wrapper(dict.__delitem__)
    pop = mark_as_changed_wrapper(dict.pop)
    clear = mark_as_changed_wrapper(dict.clear)
    update = mark_as_changed_wrapper(dict.update)
    popitem = mark_as_changed_wrapper(dict.popitem)
    setdefault = mark_as_changed_wrapper(dict.setdefault)

    def _mark_as_changed(self, key=None):
        if hasattr(self._instance, "_mark_as_changed"):
            if key:
                self._instance._mark_as_changed(f"{self._name}.{key}")
            else:
                self._instance._mark_as_changed(self._name)


class BaseList(list):
    """A special list so we can watch any changes."""

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, list_items, instance, name):
        BaseDocument = _import_class("BaseDocument")

        if isinstance(instance, BaseDocument):
            self._instance = weakref.proxy(instance)
        self._name = name
        super().__init__(list_items)

    def __getitem__(self, key):
        # change index to positive value because MongoDB does not support negative one
        if isinstance(key, int) and key < 0:
            key = len(self) + key
        value = super().__getitem__(key)

        if isinstance(key, slice):
            # When receiving a slice operator, we don't convert the structure and bind
            # to parent's instance. This is buggy for now but would require more work to be handled properly
            return value

        EmbeddedDocument = _import_class("EmbeddedDocument")
        if isinstance(value, EmbeddedDocument) and value._instance is None:
            value._instance = self._instance
        elif isinstance(value, dict) and not isinstance(value, BaseDict):
            # Replace dict by BaseDict
            value = BaseDict(value, None, f"{self._name}.{key}")
            super().__setitem__(key, value)
            value._instance = self._instance
        elif isinstance(value, list) and not isinstance(value, BaseList):
            # Replace list by BaseList
            value = BaseList(value, None, f"{self._name}.{key}")
            super().__setitem__(key, value)
            value._instance = self._instance
        return value

    def __iter__(self):
        yield from super().__iter__()

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    def __setitem__(self, key, value):
        changed_key = key
        if isinstance(key, slice):
            # In case of slice, we don't bother to identify the exact elements being updated
            # instead, we simply marks the whole list as changed
            changed_key = None

        result = super().__setitem__(key, value)
        self._mark_as_changed(changed_key)
        return result

    append = mark_as_changed_wrapper(list.append)
    extend = mark_as_changed_wrapper(list.extend)
    insert = mark_as_changed_wrapper(list.insert)
    pop = mark_as_changed_wrapper(list.pop)
    remove = mark_as_changed_wrapper(list.remove)
    reverse = mark_as_changed_wrapper(list.reverse)
    sort = mark_as_changed_wrapper(list.sort)
    __delitem__ = mark_as_changed_wrapper(list.__delitem__)
    __iadd__ = mark_as_changed_wrapper(list.__iadd__)
    __imul__ = mark_as_changed_wrapper(list.__imul__)

    def _mark_as_changed(self, key=None):
        if hasattr(self._instance, "_mark_as_changed"):
            if key is not None:
                self._instance._mark_as_changed(f"{self._name}.{key % len(self)}")
            else:
                self._instance._mark_as_changed(self._name)


class EmbeddedDocumentList(BaseList):
    def __init__(self, list_items, instance, name):
        super().__init__(list_items, instance, name)
        self._instance = instance

    @classmethod
    def __match_all(cls, embedded_doc, kwargs):
        """Return True if a given embedded doc matches all the filter
        kwargs. If it doesn't return False.
        """
        for key, expected_value in kwargs.items():
            doc_val = getattr(embedded_doc, key)
            if doc_val != expected_value and str(doc_val) != expected_value:
                return False
        return True

    @classmethod
    def __only_matches(cls, embedded_docs, kwargs):
        """Return embedded docs that match the filter kwargs."""
        if not kwargs:
            return embedded_docs
        return [doc for doc in embedded_docs if cls.__match_all(doc, kwargs)]

    def filter(self, **kwargs):
        """
        Filters the list by only including embedded documents with the
        given keyword arguments.

        This method only supports simple comparison (e.g. .filter(name='John Doe'))
        and does not support operators like __gte, __lte, __icontains like queryset.filter does

        :param kwargs: The keyword arguments corresponding to the fields to
         filter on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: A new ``EmbeddedDocumentList`` containing the matching
         embedded documents.

        Raises ``AttributeError`` if a given keyword is not a valid field for
        the embedded document class.
        """
        values = self.__only_matches(self, kwargs)
        return EmbeddedDocumentList(values, self._instance, self._name)

    def exclude(self, **kwargs):
        """
        Filters the list by excluding embedded documents with the given
        keyword arguments.

        :param kwargs: The keyword arguments corresponding to the fields to
         exclude on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: A new ``EmbeddedDocumentList`` containing the non-matching
         embedded documents.

        Raises ``AttributeError`` if a given keyword is not a valid field for
        the embedded document class.
        """
        exclude = self.__only_matches(self, kwargs)
        values = [item for item in self if item not in exclude]
        return EmbeddedDocumentList(values, self._instance, self._name)

    def count(self):
        """
        The number of embedded documents in the list.

        :return: The length of the list, equivalent to the result of ``len()``.
        """
        return len(self)

    def get(self, **kwargs):
        """
        Retrieves an embedded document determined by the given keyword
        arguments.

        :param kwargs: The keyword arguments corresponding to the fields to
         search on. *Multiple arguments are treated as if they are ANDed
         together.*
        :return: The embedded document matched by the given keyword arguments.

        Raises ``DoesNotExist`` if the arguments used to query an embedded
        document returns no results. ``MultipleObjectsReturned`` if more
        than one result is returned.
        """
        values = self.__only_matches(self, kwargs)
        if len(values) == 0:
            raise DoesNotExist("%s matching query does not exist." % self._name)
        elif len(values) > 1:
            raise MultipleObjectsReturned(
                "%d items returned, instead of 1" % len(values)
            )

        return values[0]

    def first(self):
        """Return the first embedded document in the list, or ``None``
        if empty.
        """
        if len(self) > 0:
            return self[0]

    def create(self, **values):
        """
        Creates a new instance of the EmbeddedDocument and appends it to this EmbeddedDocumentList.

        .. note::
            the instance of the EmbeddedDocument is not automatically saved to the database.
            You still need to call .save() on the parent Document.

        :param values: A dictionary of values for the embedded document.
        :return: The new embedded document instance.
        """
        name = self._name
        EmbeddedClass = self._instance._fields[name].field.document_type_obj
        self._instance[self._name].append(EmbeddedClass(**values))

        return self._instance[self._name][-1]

    def save(self, *args, **kwargs):
        """
        Saves the ancestor document.

        :param args: Arguments passed up to the ancestor Document's save
         method.
        :param kwargs: Keyword arguments passed up to the ancestor Document's
         save method.
        """
        self._instance.save(*args, **kwargs)

    def delete(self):
        """
        Deletes the embedded documents from the database.

        .. note::
            The embedded document changes are not automatically saved
            to the database after calling this method.

        :return: The number of entries deleted.
        """
        values = list(self)
        for item in values:
            self._instance[self._name].remove(item)

        return len(values)

    def update(self, **update):
        """
        Updates the embedded documents with the given replacement values. This
        function does not support mongoDB update operators such as ``inc__``.

        .. note::
            The embedded document changes are not automatically saved
            to the database after calling this method.

        :param update: A dictionary of update values to apply to each
         embedded document.
        :return: The number of entries updated.
        """
        if len(update) == 0:
            return 0
        values = list(self)
        for item in values:
            for k, v in update.items():
                setattr(item, k, v)

        return len(values)


class StrictDict:
    __slots__ = ()
    _special_fields = {"get", "pop", "iteritems", "items", "keys", "create"}
    _classes = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        key = "_reserved_" + key if key in self._special_fields else key
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        key = "_reserved_" + key if key in self._special_fields else key
        return setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key, default=None):
        v = self.get(key, default)
        try:
            delattr(self, key)
        except AttributeError:
            pass
        return v

    def iteritems(self):
        for key in self:
            yield key, self[key]

    def items(self):
        return [(k, self[k]) for k in iter(self)]

    def iterkeys(self):
        return iter(self)

    def keys(self):
        return list(iter(self))

    def __iter__(self):
        return (key for key in self.__slots__ if hasattr(self, key))

    def __len__(self):
        return len(list(self.items()))

    def __eq__(self, other):
        return list(self.items()) == list(other.items())

    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def create(cls, allowed_keys):
        allowed_keys_tuple = tuple(
            ("_reserved_" + k if k in cls._special_fields else k) for k in allowed_keys
        )
        allowed_keys = frozenset(allowed_keys_tuple)
        if allowed_keys not in cls._classes:

            class SpecificStrictDict(cls):
                __slots__ = allowed_keys_tuple

                def __repr__(self):
                    return "{%s}" % ", ".join(
                        f'"{k!s}": {v!r}' for k, v in self.items()
                    )

            cls._classes[allowed_keys] = SpecificStrictDict
        return cls._classes[allowed_keys]


class LazyReference(DBRef):
    __slots__ = ("_cached_doc", "passthrough", "document_type")

    def fetch(self, force=False):
        if not self._cached_doc or force:
            self._cached_doc = self.document_type.objects.get(pk=self.pk)
            if not self._cached_doc:
                raise DoesNotExist("Trying to dereference unknown document %s" % (self))
        return self._cached_doc

    @property
    def pk(self):
        return self.id

    def __init__(self, document_type, pk, cached_doc=None, passthrough=False):
        self.document_type = document_type
        self._cached_doc = cached_doc
        self.passthrough = passthrough
        super().__init__(self.document_type._get_collection_name(), pk)

    def __getitem__(self, name):
        if not self.passthrough:
            raise KeyError()
        document = self.fetch()
        return document[name]

    def __getattr__(self, name):
        if not object.__getattribute__(self, "passthrough"):
            raise AttributeError()
        document = self.fetch()
        try:
            return document[name]
        except KeyError:
            raise AttributeError()

    def __repr__(self):
        return f"<LazyReference({self.document_type}, {self.pk!r})>"
