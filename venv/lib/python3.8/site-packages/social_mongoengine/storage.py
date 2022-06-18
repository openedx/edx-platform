import base64
import six

from mongoengine import DictField, IntField, StringField, \
                        EmailField, BooleanField
from mongoengine.queryset import OperationError

from social_core.storage import UserMixin, AssociationMixin, NonceMixin, \
                                CodeMixin, PartialMixin, BaseStorage


UNUSABLE_PASSWORD = '!'  # Borrowed from django 1.4


class MongoengineUserMixin(UserMixin):
    """Social Auth association model"""
    user = None
    provider = StringField(max_length=32)
    uid = StringField(max_length=255, unique_with='provider')
    extra_data = DictField()

    def str_id(self):
        return str(self.id)

    @classmethod
    def get_social_auth_for_user(cls, user, provider=None, id=None):
        qs = cls.objects
        if provider:
            qs = qs.filter(provider=provider)
        if id:
            qs = qs.filter(id=id)
        return qs.filter(user=user.id)

    @classmethod
    def create_social_auth(cls, user, uid, provider):
        if not isinstance(type(uid), six.string_types):
            uid = str(uid)
        return cls.objects.create(user=user.id, uid=uid, provider=provider)

    @classmethod
    def username_max_length(cls):
        username_field = cls.username_field()
        field = getattr(cls.user_model(), username_field)
        return field.max_length

    @classmethod
    def username_field(cls):
        return getattr(cls.user_model(), 'USERNAME_FIELD', 'username')

    @classmethod
    def create_user(cls, *args, **kwargs):
        kwargs['password'] = UNUSABLE_PASSWORD
        if 'email' in kwargs:
            # Empty string makes email regex validation fail
            kwargs['email'] = kwargs['email'] or None
        return cls.user_model().objects.create(*args, **kwargs)

    @classmethod
    def allowed_to_disconnect(cls, user, backend_name, association_id=None):
        if association_id is not None:
            qs = cls.objects.filter(id__ne=association_id)
        else:
            qs = cls.objects.filter(provider__ne=backend_name)
        qs = qs.filter(user=user)

        if hasattr(user, 'has_usable_password'):
            valid_password = user.has_usable_password()
        else:
            valid_password = True

        return valid_password or qs.count() > 0

    @classmethod
    def changed(cls, user):
        user.save()

    def set_extra_data(self, extra_data=None):
        if super(MongoengineUserMixin, self).set_extra_data(extra_data):
            self.save()

    @classmethod
    def disconnect(cls, entry):
        entry.delete()

    @classmethod
    def user_exists(cls, *args, **kwargs):
        """
        Return True/False if a User instance exists with the given arguments.
        Arguments are directly passed to filter() manager method.
        """
        if 'username' in kwargs:
            kwargs[cls.username_field()] = kwargs.pop('username')
        return cls.user_model().objects.filter(*args, **kwargs).count() > 0

    @classmethod
    def get_username(cls, user):
        return getattr(user, cls.username_field(), None)

    @classmethod
    def get_user(cls, pk):
        try:
            return cls.user_model().objects.get(id=pk)
        except cls.user_model().DoesNotExist:
            return None

    @classmethod
    def get_users_by_email(cls, email):
        return cls.user_model().objects.filter(email__iexact=email)

    @classmethod
    def get_social_auth(cls, provider, uid):
        if not isinstance(uid, six.string_types):
            uid = str(uid)
        try:
            return cls.objects.get(provider=provider, uid=uid)
        except cls.DoesNotExist:
            return None


class MongoengineNonceMixin(NonceMixin):
    """One use numbers"""
    server_url = StringField(max_length=255)
    timestamp = IntField()
    salt = StringField(max_length=40)

    @classmethod
    def use(cls, server_url, timestamp, salt):
        return cls.objects.get_or_create(server_url=server_url,
                                         timestamp=timestamp,
                                         salt=salt)[1]


class MongoengineAssociationMixin(AssociationMixin):
    """OpenId account association"""
    server_url = StringField(max_length=255)
    handle = StringField(max_length=255)
    secret = StringField(max_length=255)  # Stored base64 encoded
    issued = IntField()
    lifetime = IntField()
    assoc_type = StringField(max_length=64)

    @classmethod
    def store(cls, server_url, association):
        # Don't use get_or_create because issued cannot be null
        try:
            assoc = cls.objects.get(server_url=server_url,
                                    handle=association.handle)
        except cls.DoesNotExist:
            assoc = cls(server_url=server_url,
                        handle=association.handle)
        assoc.secret = base64.encodestring(association.secret)
        assoc.issued = association.issued
        assoc.lifetime = association.lifetime
        assoc.assoc_type = association.assoc_type
        assoc.save()

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.filter(*args, **kwargs)

    @classmethod
    def remove(cls, ids_to_delete):
        cls.objects.filter(pk__in=ids_to_delete).delete()


class MongoengineCodeMixin(CodeMixin):
    email = EmailField()
    code = StringField(max_length=32)
    verified = BooleanField(default=False)

    @classmethod
    def get_code(cls, code):
        try:
            return cls.objects.get(code=code)
        except cls.DoesNotExist:
            return None


class MongoenginePartialMixin(PartialMixin):
    token = StringField(max_length=32)
    data = DictField()
    extra_data = DictField()
    next_step = IntField()
    backend = StringField(max_length=32)

    @classmethod
    def load(cls, token):
        try:
            return cls.objects.get(token=token)
        except cls.DoesNotExist:
            return None

    @classmethod
    def destroy(cls, token):
        partial = cls.load(token)
        if partial:
            partial.delete()


class BaseMongoengineStorage(BaseStorage):
    user = MongoengineUserMixin
    nonce = MongoengineNonceMixin
    association = MongoengineAssociationMixin
    code = MongoengineCodeMixin
    partial = MongoenginePartialMixin

    @classmethod
    def is_integrity_error(cls, exception):
        return exception.__class__ is OperationError and \
               'E11000' in exception.message
