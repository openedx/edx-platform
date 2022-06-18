"""
The standard way of using djongo is to import models.py
in place of Django's standard models module.

Djongo Fields is where custom fields for working with
MongoDB is defined.

 - EmbeddedField
 - ArrayField
 - ArrayReferenceField
 - GenericReferenceField

These are the main fields for working with MongoDB.
"""

import functools
import json
import typing

from bson import ObjectId
from django import forms
from django.core.exceptions import ValidationError
from django.db import connections as pymongo_connections
from django.db import router, connections, transaction
from django.db.models import (
    Manager, Model, Field, AutoField,
    ForeignKey, BigAutoField)
from django.utils import version
from django.db.models.fields.related import RelatedField
from django.forms import modelform_factory
from django.utils.functional import cached_property
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from djongo.exceptions import NotSupportedError, print_warn

django_major = int(version.get_version().split('.')[0])

if django_major >= 3:
    from django.db.models.fields import AutoFieldMixin, AutoFieldMeta


def make_mdl(model, model_dict):
    """
    Builds an instance of model from the model_dict.
    """
    for field_name in model_dict:
        field = model._meta.get_field(field_name)
        model_dict[field_name] = field.to_python(model_dict[field_name])

    return model(**model_dict)


def useful_field(field):
    return field.concrete and not isinstance(field, (AutoField, BigAutoField))


class DjongoManager(Manager):
    """
    This modified manager allows to issue Mongo functions by prefixing
    them with 'mongo_'.

    This module allows methods to be passed directly to pymongo.
    """

    def __getattr__(self, name):
        if name.startswith('mongo'):
            name = name[6:]
            return getattr(self._client, name)
        else:
            return super().__getattr__(name)

    @property
    def _client(self):
        return (pymongo_connections[self.db]
                .cursor()
                .db_conn[self.model._meta.db_table])


class MongoField(Field):
    empty_strings_allowed = False


class JSONField(MongoField):
    def get_prep_value(self, value):
        if not isinstance(value, (dict, list)):
            raise ValueError(
                f'Value: {value} must be of type dict/list'
            )
        return value

    def to_python(self, value):
        if not isinstance(value, (dict, list)):
            raise ValueError(
                f'Value: {value} stored in DB must be of type dict/list'
                'Did you miss any Migrations?'
            )
        return value


class ModelField(MongoField):
    """
    Allows for the inclusion of an instance of an abstract model as
    a field inside a document.
    """
    base_type = dict

    def __init__(self,
                 model_container: typing.Type[Model],
                 *args, **kwargs):
        self.model_container = model_container
        self._validate_container()
        super().__init__(*args, **kwargs)

    def _validate_container(self):
        for field in self.model_container._meta._get_fields(reverse=False):
            if isinstance(field, (AutoField,
                                  BigAutoField,
                                  RelatedField)):
                raise ValidationError(
                    f'Field "{field}" of model container:"{self.model_container}" '
                    f'cannot be of type "{type(field)}"')

            if field.attname != field.column:
                raise ValidationError(
                    f'Field "{field}"  of model container:"{self.model_container}" '
                    f'cannot be named as "{field.attname}", different from '
                    f'column name "{field.column}"')

            if field.db_index:
                print_warn('Embedded field index')
                raise NotSupportedError(
                    f'This version of djongo does not support indexes on embedded fields'
                )

    def _value_thru_fields(self,
                           func_name: str,
                           value: dict,
                           *other_args):
        processed_value = {}
        for field in self.model_container._meta.get_fields():
            try:
                field_value = value[field.attname]
            except KeyError:
                continue
            processed_value[field.attname] = getattr(field, func_name)(field_value, *other_args)
        return processed_value
    
    def _save_value_thru_fields(self,
                                func_name: str,
                                value: dict,
                                *other_args):
        processed_value = {}
        errors = {}
        for field in self.model_container._meta.get_fields():
            try:
                try:
                    field_value = value[field.attname]
                except KeyError:
                    raise ValidationError(f'Value for field "{field}" not supplied')
                processed_value[field.attname] = getattr(field, func_name)(field_value, *other_args)
            except ValidationError as e:
                errors[field.name] = e.error_list

        if errors:
            e = ValidationError(errors)
            raise ValidationError(str(e))

        return processed_value

    def _obj_thru_fields(self,
                         func_name: str,
                         obj: Model,
                         *other_args):
        processed_value = {}
        for field in self.model_container._meta.get_fields():
            processed_value[field.attname] = getattr(field, func_name)(obj, *other_args)
        return processed_value

    def _value_thru_container(self, value):
        processed_value = {}
        inst = self.model_container(**value)
        for field in self.model_container._meta.get_fields():
            processed_value[field.attname] = getattr(inst, field.attname)
        return processed_value

    def validate(self, value, model_instance, validate_parent=True):
        if validate_parent:
            super().validate(value, model_instance)

        if value is None:
            super().validate(value, model_instance)
            return

        container_instance = self.model_container(**value)
        self._value_thru_fields('validate', value, container_instance)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            raise TypeError(f'Type: {type(value)} cannot be serialized')

        container_obj = self.model_container(**value)
        processed_value = self._obj_thru_fields('value_to_string', container_obj)
        return json.dumps(processed_value)

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        if value is None:
            return None

        container_obj = self.model_container(**value)
        processed_value = self._obj_thru_fields('value_from_object', container_obj)
        return processed_value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['model_container'] = self.model_container
        return name, path, args, kwargs

    def get_db_prep_save(self, value, connection):
        if value is None:
            return None

        if not isinstance(value, self.base_type):
            raise ValueError(
                f'Value: {value} must be an instance of {self.base_type}')

        processed_value = self._save_value_thru_fields('get_db_prep_save',
                                                       value, 
                                                       connection)
        return processed_value
     
    def get_prep_value(self, value):
        if (value is None or
                not isinstance(value, self.base_type)):
            return value

        processed_value = self._value_thru_fields('get_prep_value',
                                                  value)
        return processed_value

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def to_python(self, value):
        """
        Overrides Django's default to_python to allow correct
        translation to instance.
        """
        if value is None:
            return None

        if isinstance(value, str):
            value = json.loads(value)

        if not isinstance(value, self.base_type):
            raise ValidationError(
                f'Value: {value} must be an instance of {self.base_type}')

        value = self._value_thru_container(value)
        processed_value = self._value_thru_fields('to_python', value)
        return processed_value


class FormedField(ModelField):

    def __init__(self,
                 model_container: typing.Type[Model],
                 model_form_class: typing.Type[forms.ModelForm] = None,
                 model_form_kwargs: dict = None,
                 *args, **kwargs):
        super().__init__(model_container, *args, **kwargs)
        self.model_form_class = model_form_class

        if model_form_kwargs is None:
            model_form_kwargs = {}
        self.model_form_kwargs = model_form_kwargs

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.model_form_class is not None:
            kwargs['model_form_class'] = self.model_form_class
        if self.model_form_kwargs:
            kwargs['model_form_kwargs'] = self.model_form_kwargs
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {
            'form_class': EmbeddedFormField,
            'model_container': self.model_container,
            'model_form_class': self.model_form_class,
            'model_form_kw': self.model_form_kwargs,
            'name': self.attname
        }

        defaults.update(kwargs)
        return super().formfield(**defaults)


class ArrayField(FormedField):
    """
    Implements an array of objects inside the document.

    The allowed object type is defined on model declaration. The
    declared instance will accept a python list of instances of the
    given model as its contents.

    The model of the container must be declared as abstract, thus should
    not be treated as a collection of its own.
    """
    empty_strings_allowed = False
    base_type = list

    def _value_thru_container(self, value):
        post_value = []
        for _dict in value:
            post_value.append(super()._value_thru_container(_dict))
        return post_value

    def _value_thru_fields(self,
                           func_name: str,
                           value: typing.Union[list, dict],
                           *other_args):
        if isinstance(value, dict):
            return super()._value_thru_fields(func_name,
                                              value,
                                              *other_args)

        processed_value = []
        for pre_dict in value:
            post_dict = super()._value_thru_fields(func_name,
                                                   pre_dict,
                                                   *other_args)
            processed_value.append(post_dict)
        return processed_value

    def _save_value_thru_fields(self,
                                func_name: str,
                                value: typing.Union[list, dict],
                                *other_args):
        processed_value = []
        for pre_dict in value:
            post_dict = super()._save_value_thru_fields(func_name,
                                                        pre_dict,
                                                        *other_args)
            processed_value.append(post_dict)
        return processed_value

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        processed_value = []
        for _dict in value:
            container_obj = self.model_container(**_dict)
            post_dict = self._obj_thru_fields('value_to_string', container_obj)
            processed_value.append(post_dict)
        return json.dumps(processed_value)

    def value_from_object(self, obj):
        value = getattr(obj, self.attname)
        processed_value = []
        for _dict in value:
            container_obj = self.model_container(**_dict)
            post_dict = self._obj_thru_fields('value_from_object', container_obj)
            processed_value.append(post_dict)
        return processed_value

    def validate(self, value, model_instance, validate_parent=True):
        super(ModelField, self).validate(value, model_instance)
        for _dict in value:
            super().validate(_dict, model_instance, validate_parent=False)


def _get_model_form_class(model_form_class, model_container, admin, request):
    if not model_form_class:
        form_kwargs = dict(
            form=forms.ModelForm,
            fields=forms.ALL_FIELDS,
        )

        if admin and request:
            form_kwargs['formfield_callback'] = functools.partial(
                admin.formfield_for_dbfield, request=request)

        model_form_class = modelform_factory(model_container, **form_kwargs)

    return model_form_class


class NestedFormSet(forms.formsets.BaseFormSet):
    def add_fields(self, form, index):
        for name, field in form.fields.items():
            if isinstance(field, ArrayFormField):
                field.name = '%s-%s' % (form.prefix, name)
        super(NestedFormSet, self).add_fields(form, index)


class ArrayFormField(forms.Field):
    def __init__(self, name, model_form_class, model_container, mdl_form_kw_l,
                 widget=None, admin=None, request=None, *args, **kwargs):

        self.name = name
        self.model_container = model_container
        self.model_form_class = _get_model_form_class(
            model_form_class, model_container, admin, request)
        self.mdl_form_kw_l = mdl_form_kw_l
        self.admin = admin
        self.request = request

        if not widget:
            widget = ArrayFormWidget(self.model_form_class.__name__)

        error_messages = {
            'incomplete': 'Enter all required fields.',
        }

        self.ArrayFormSet = forms.formset_factory(
            self.model_form_class, formset=NestedFormSet, can_delete=True)
        super().__init__(error_messages=error_messages,
                         widget=widget, *args, **kwargs)

    def clean(self, value):
        if not value:
            return []

        form_set = self.ArrayFormSet(value, prefix=self.name)
        if form_set.is_valid():
            ret = []
            for itm in form_set.cleaned_data:
                if itm.get('DELETE', True):
                    continue
                itm.pop('DELETE')
                ret.append(self.model_form_class._meta.model(**itm))
            return ret

        else:
            raise ValidationError(form_set.errors + form_set.non_form_errors())

    def has_changed(self, initial, data):
        form_set_initial = []
        for init in initial or []:
            form_set_initial.append(
                forms.model_to_dict(
                    init,
                    fields=self.model_form_class._meta.fields,
                    exclude=self.model_form_class._meta.exclude
                )
            )
        form_set = self.ArrayFormSet(data, initial=form_set_initial, prefix=self.name)
        return form_set.has_changed()

    def get_bound_field(self, form, field_name):
        return ArrayFormBoundField(form, self, field_name)


class ArrayFormBoundField(forms.BoundField):
    def __init__(self, form, field, name):
        super().__init__(form, field, name)

        data = self.data if form.is_bound else None
        initial = []
        if self.initial is not None:
            for ini in self.initial:
                if isinstance(ini, Model):
                    initial.append(
                        forms.model_to_dict(
                            ini,
                            fields=field.model_form_class._meta.fields,
                            exclude=field.model_form_class._meta.exclude
                        ))

        self.form_set = field.ArrayFormSet(data, initial=initial, prefix=self.html_name)

    def __getitem__(self, idx):
        if not isinstance(idx, (int, slice)):
            raise TypeError
        return self.form_set[idx]

    def __iter__(self):
        for form in self.form_set:
            yield form

    def __str__(self):
        table = format_html_join(
            '\n', '<tbody>{}</tbody>',
            ((form.as_table(),)
             for form in self.form_set))
        table = format_html(
            '\n<table class="{}-array-model-field">'
            '\n{}'
            '\n</table>',
            self.name,
            table)
        return format_html('{}\n{}', table, self.form_set.management_form)

    def __len__(self):
        return len(self.form_set)


class ArrayFormWidget(forms.Widget):
    def __init__(self, first_field_id, attrs=None):
        self.first_field_id = first_field_id
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        assert False

    def id_for_label(self, id_):
        return '{}-0-{}'.format(id_, self.first_field_id)

    def value_from_datadict(self, data, files, name):
        ret = {key: data[key] for key in data if key.startswith(name)}
        return ret

    def value_omitted_from_data(self, data, files, name):
        for key in data:
            if key.startswith(name):
                return False
        return True


class EmbeddedField(FormedField):
    pass


class EmbeddedFormField(forms.MultiValueField):
    def __init__(self, name, model_form_class, model_form_kw, model_container,
                 admin=None, request=None, *args, **kwargs):
        form_fields = []
        mdl_form_field_names = []
        widgets = []
        model_form_kwargs = model_form_kw.copy()

        try:
            model_form_kwargs['prefix'] = model_form_kwargs['prefix'] + '-' + name
        except KeyError:
            model_form_kwargs['prefix'] = name

        initial = kwargs.pop('initial', None)
        if initial:
            model_form_kwargs['initial'] = initial

        self.model_form_class = _get_model_form_class(
            model_form_class, model_container, admin, request)
        self.model_form_kwargs = model_form_kwargs
        self.admin = admin
        self.request = request

        error_messages = {
            'incomplete': 'Enter all required fields.',
        }

        self.model_form = self.model_form_class(**model_form_kwargs)
        for field_name, field in self.model_form.fields.items():
            if isinstance(field, (forms.ModelChoiceField, forms.ModelMultipleChoiceField)):
                continue
            elif isinstance(field, ArrayFormField):
                field.name = '%s-%s' % (self.model_form.prefix, field_name)
            form_fields.append(field)
            mdl_form_field_names.append(field_name)
            widgets.append(field.widget)

        widget = EmbeddedFormWidget(mdl_form_field_names, widgets)
        super().__init__(error_messages=error_messages, fields=form_fields,
                         widget=widget, require_all_fields=False, *args, **kwargs)

    def compress(self, clean_data_vals):
        model_field = dict(zip(self.model_form.fields.keys(), clean_data_vals))
        return self.model_form._meta.model(**model_field)

    def get_bound_field(self, form, field_name):
        if form.prefix:
            self.model_form.prefix = '{}-{}'.format(form.prefix, self.model_form.prefix)
        return EmbeddedFormBoundField(form, self, field_name)

    def bound_data(self, data, initial):
        if self.disabled:
            return initial
        return self.compress(data)


class EmbeddedFormBoundField(forms.BoundField):
    # def __getitem__(self, name):
    #     return self.field.model_form[name]
    #
    # def __getattr__(self, name):
    #     return getattr(self.field.model_form, name)

    def __str__(self):
        instance = self.value()
        model_form = self.field.model_form_class(instance=instance, **self.field.model_form_kwargs)

        return mark_safe(f'<table>\n{ model_form.as_table() }\n</table>')


class EmbeddedFormWidget(forms.MultiWidget):
    def __init__(self, field_names, *args, **kwargs):
        self.field_names = field_names
        super().__init__(*args, **kwargs)

    def decompress(self, value):
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, Model):
            return [getattr(value, f_n) for f_n in self.field_names]
        else:
            raise forms.ValidationError('Expected model-form')

    def value_from_datadict(self, data, files, name):
        ret = []
        for i, wid in enumerate(self.widgets):
            f_n = '{}-{}'.format(name, self.field_names[i])
            ret.append(wid.value_from_datadict(
                data, files, f_n
            ))
        return ret

    def value_omitted_from_data(self, data, files, name):
        return all(
            widget.value_omitted_from_data(
                data, files, '{}-{}'.format(name, self.field_names[i])
            )
            for i, widget in enumerate(self.widgets)
        )


class ObjectIdFieldMixin:
    description = _("ObjectId")
    empty_strings_allowed = False

    def get_db_prep_value(self, value, connection, prepared=False):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, str):
            return ObjectId(value)
        return value

    def get_internal_type(self):
        return "ObjectIdField"

    def rel_db_type(self, connection):
        return self.db_type(connection)

    def get_prep_value(self, value):
        return value


class GenericObjectIdField(ObjectIdFieldMixin, Field):
    pass


if django_major >= 3:
    class _ObjectIdField(AutoFieldMixin, GenericObjectIdField, metaclass=AutoFieldMeta):
        pass
else:
    class _ObjectIdField(ObjectIdFieldMixin, AutoField):
        pass


class ObjectIdField(_ObjectIdField):
    """
    For every document inserted into a collection MongoDB internally creates an field.
    The field can be referenced from within the Model as _id.
    """

    def __init__(self, *args, **kwargs):
        id_field_args = {
            'primary_key': True,
            'auto_created': True
        }
        id_field_args.update(kwargs)
        super().__init__(*args, **id_field_args)


class ArrayReferenceManagerMixin:

    def _apply_rel_filters(self, queryset):
        """
        Filter the queryset for the instance this manager is bound to.
        """
        queryset._add_hints(instance=self.instance)
        if self._db:
            queryset = queryset.using(self._db)
        queryset = queryset.filter(**self.core_filters)

        return queryset

    def get_queryset(self):
        try:
            return self.instance._prefetched_objects_cache[self.field.related_query_name()]
        except (AttributeError, KeyError):
            queryset = super().get_queryset()
            return self._apply_rel_filters(queryset)

    def update_or_create(self, **kwargs):
        db = router.db_for_write(self.instance.__class__, instance=self.instance)
        obj, created = super(ArrayReferenceManagerMixin, self.db_manager(db)).update_or_create(**kwargs)
        # We only need to add() if created because if we got an object back
        # from get() then the relationship already exists.
        if created:
            self.add(obj)
        return obj, created

    update_or_create.alters_data = True

    def get_or_create(self, **kwargs):
        db = router.db_for_write(self.instance.__class__, instance=self.instance)
        obj, created = super(ArrayReferenceManagerMixin, self.db_manager(db)).get_or_create(**kwargs)
        # We only need to add() if created because if we got an object back
        # from get() then the relationship already exists.
        if created:
            self.add(obj)
        return obj, created

    get_or_create.alters_data = True

    def create(self, **kwargs):
        db = router.db_for_write(self.instance.__class__, instance=self.instance)
        new_obj = super(ArrayReferenceManagerMixin, self.db_manager(db)).create(**kwargs)
        self.add(new_obj)
        return new_obj

    create.alters_data = True


def create_reverse_array_reference_manager(superclass, rel):
    if issubclass(superclass, DjongoManager):
        baseclass = superclass
    else:
        baseclass = type('baseclass', (DjongoManager, superclass), {})

    class ReverseArrayReferenceManager(ArrayReferenceManagerMixin, baseclass):
        def __init__(self, instance):
            super().__init__()
            self.instance = instance
            self.model = rel.related_model
            self.field = rel.remote_field

            name = rel.remote_field.name
            self.core_filters = {name: instance}

        def __call__(self, *, manager):
            manager = getattr(self.model, manager)
            manager_class = create_reverse_array_reference_manager(manager.__class__, rel)
            return manager_class(instance=self.instance)

        do_not_call_in_templates = True

        def _apply_rel_filters(self, queryset):
            queryset = super()._apply_rel_filters(queryset)
            db = self._db or router.db_for_read(self.model, instance=self.instance)
            empty_strings_as_null = connections[db].features.interprets_empty_strings_as_nulls

            for field in self.field.foreign_related_fields:
                val = getattr(self.instance, field.attname)
                if val is None or (val == '' and empty_strings_as_null):
                    return queryset.none()
            return queryset

        def _make_filter(self, *objs):
            ids = set(obj.pk for obj in objs)
            return {
                self.model._meta.pk.name: {
                    '$in': list(ids)
                }
            }

        def add(self, *objs):
            _filter = self._make_filter(*objs)
            lh_field, rh_field = self.field.related_fields[0]
            self.mongo_update(
                _filter,
                {
                    '$addToSet': {
                        lh_field.get_attname():
                            getattr(self.instance, rh_field.get_attname())
                    }
                }
            )
            for obj in objs:
                fk_field = getattr(obj, lh_field.get_attname())
                fk_field.add(getattr(self.instance, rh_field.get_attname()))

        add.alters_data = True

        def remove(self, *objs):
            pass

        remove.alters_data = True

        def clear(self):
            pass

        clear.alters_data = True

        def set(self, objs, *, clear=False):
            pass

        set.alters_data = True

        def create(self, **kwargs):
            pass

        create.alters_data = True

    return ReverseArrayReferenceManager


def create_forward_array_reference_manager(superclass, rel):
    if issubclass(superclass, DjongoManager):
        baseclass = superclass
    else:
        baseclass = type('baseclass', (DjongoManager, superclass), {})

    class ArrayReferenceManager(ArrayReferenceManagerMixin, baseclass):

        def __init__(self, instance):
            super().__init__()

            self.instance = instance
            self.model = rel.model
            self.field = rel.remote_field
            self.instance_manager = DjongoManager()
            self.instance_manager.model = instance
            name = self.field.related_fields[0][1].attname
            ids = getattr(instance, self.field.attname) or []

            self.core_filters = {f'{name}__in': ids}

        def __call__(self, *, manager):
            manager = getattr(self.model, manager)
            manager_class = create_forward_array_reference_manager(manager.__class__, rel)
            return manager_class(instance=self.instance)

        do_not_call_in_templates = True

        def _apply_rel_filters(self, queryset):
            queryset = super()._apply_rel_filters(queryset)
            if not getattr(self.instance, self.field.attname):
                return queryset.none()
            return queryset

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[self.field.related_query_name()]
            except (AttributeError, KeyError):
                queryset = super().get_queryset()
                return self._apply_rel_filters(queryset)

        def _make_filter(self):
            return {self.instance._meta.pk.name: self.instance.pk}

        def add(self, *objs):
            fks = getattr(self.instance, self.field.get_attname())
            if fks is None:
                fks = set()
                setattr(self.instance, self.field.get_attname(), fks)

            new_fks = set()
            rh_field = self.field.foreign_related_fields[0]
            for obj in objs:
                new_fks.add(getattr(obj, rh_field.get_attname()))
            fks.update(new_fks)

            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            self.instance_manager.db_manager(db).mongo_update(
                self._make_filter(),
                {
                    '$addToSet': {
                        self.field.attname: {
                            '$each': list(new_fks)
                        }
                    }
                }
            )

        add.alters_data = True

        def remove(self, *objs):
            to_del = set(
                getattr(obj, self.field.foreign_related_fields[0].attname)
                for obj in objs
            )
            self._remove(to_del)

        remove.alters_data = True

        def _remove(self, to_del):
            fks = getattr(self.instance, self.field.attname)
            fks.difference_update(to_del)
            db = self._db or router.db_for_write(self.instance.__class__, instance=self.instance)
            self.instance_manager.db_manager(db).mongo_update(
                self._make_filter(),
                {
                    '$pull': {
                        self.field.attname: {
                            '$in': list(to_del)
                        }
                    }
                }
            )

        def clear(self):
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            self.instance_manager.db_manager(db).mongo_update(
                self._make_filter(),
                {
                    '$set': {
                        self.field.attname: []
                    }
                }
            )
            setattr(self.instance, self.field.attname, set())

        clear.alters_data = True

        def set(self, objs, *, clear=False):
            objs = tuple(objs)

            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                if clear:
                    self.clear()
                    self.add(*objs)
                else:
                    fks = getattr(self.instance, self.field.attname)
                    rh_field = self.field.foreign_related_fields[0]
                    new_fks = set(getattr(obj, rh_field.get_attname()) for obj in objs)
                    to_del = fks - new_fks
                    self._remove(to_del)
                    fks = getattr(self.instance, self.field.attname)
                    to_add = []
                    for obj in objs:
                        if getattr(obj, rh_field.get_attname()) not in fks:
                            to_add.append(obj)
                    self.add(to_add)

        set.alters_data = True

    return ArrayReferenceManager


class ArrayReferenceDescriptor:

    def __init__(self, field_with_rel):
        self.field = field_with_rel

    @cached_property
    def related_manager_cls(self):
        related_model = self.field.related_model

        return create_forward_array_reference_manager(
            related_model._default_manager.__class__,
            self.field.remote_field,
        )

    def __get__(self, instance, cls=None):
        """
        Get the related objects through the reverse relation.

        With the example above, when getting ``parent.children``:

        - ``self`` is the descriptor managing the ``children`` attribute
        - ``instance`` is the ``parent`` instance
        - ``cls`` is the ``Parent`` class (unused)
        """
        if instance is None:
            return self

        return self.related_manager_cls(instance)


class ReverseArrayReferenceDescriptor:

    def __init__(self, related):
        self.rel = related

    @cached_property
    def related_manager_cls(self):
        related_model = self.rel.related_model

        return create_reverse_array_reference_manager(
            related_model._default_manager.__class__,
            self.rel,
        )

    def __get__(self, instance, cls=None):
        """
        Get the related objects through the relation.

        With the example above, when getting ``parent.children``:

        - ``self`` is the descriptor managing the ``children`` attribute
        - ``instance`` is the ``parent`` instance
        - ``cls`` is the ``Parent`` class (unused)
        """
        if instance is None:
            return self

        return self.related_manager_cls(instance)


# class ArrayManyToManyField(ManyToManyField):
#
#     def contribute_to_class(self, cls, name, **kwargs):
#         super().contribute_to_class(cls, name, **kwargs)
#         setattr(cls, self.name, ArrayManyToManyDescriptor(self.remote_field, reverse=False))


class ArrayReferenceField(ForeignKey):
    """
    When the entry gets saved, only a reference to the primary_key of the model is saved in the array.
    For all practical aspects, the ArrayReferenceField behaves like a Django ManyToManyField.
    """

    many_to_many = False
    many_to_one = True
    one_to_many = False
    one_to_one = False
    # rel_class = ManyToManyRel
    related_accessor_class = ReverseArrayReferenceDescriptor
    forward_related_accessor_class = ArrayReferenceDescriptor

    def __init__(self, to, on_delete=None, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):

        on_delete = on_delete or self._on_delete
        super().__init__(to, on_delete=on_delete, related_name=related_name,
                         related_query_name=related_query_name,
                         limit_choices_to=limit_choices_to,
                         parent_link=parent_link, to_field=to_field,
                         db_constraint=db_constraint, **kwargs)

        self.concrete = False

    @staticmethod
    def _on_delete(collector, field, sub_objs, using):
        for model, instances in collector.data.items():
            for obj in sub_objs:
                getattr(obj, field.name).db_manager(using).remove(*instances)

    def from_db_value(self, value, expression, connection, context=None):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return set()
        return set(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return []
        elif isinstance(value, set):
            return list(value)
        return value
        # return super().get_db_prep_value(value, connection, prepared)

    def get_db_prep_save(self, value, connection):
        return self.get_db_prep_value(value, connection)
        # if value is None:
        #     return []
        # return list(value)

    def validate(self, value, model_instance):
        pass
        # super().validate(list(value), model_instance)

    def save_form_data(self, instance, data):
        getattr(instance, self.name).set(list(data), clear=True)

    def formfield(self, *, using=None, **kwargs):
        defaults = {
            'form_class': forms.ModelMultipleChoiceField,
            'queryset': self.remote_field.model._default_manager.using(using),
            **kwargs,
        }
        # If initial is passed in, it's a list of related objects, but the
        # MultipleChoiceField takes a list of IDs.
        if defaults.get('initial') is not None:
            initial = defaults['initial']
            if callable(initial):
                initial = initial()
            defaults['initial'] = [i.pk for i in initial]
        return super().formfield(**defaults)
