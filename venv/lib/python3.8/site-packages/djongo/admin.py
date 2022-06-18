import copy

from django.contrib import admin
from djongo.models import fields


class ModelAdmin(admin.ModelAdmin):
    DJONGO_FIELDS = (
        fields.ArrayField,
        fields.EmbeddedField,
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if not isinstance(db_field, self.DJONGO_FIELDS):
            return admin.ModelAdmin.formfield_for_dbfield(
                self, db_field, request, **kwargs)

        admin_instance = ModelAdmin(db_field.model_container, admin.site)
        kwargs.setdefault('admin', admin_instance)
        kwargs.setdefault('request', request)

        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                kwargs = dict(copy.deepcopy(
                    self.formfield_overrides[klass]), **kwargs)

        return db_field.formfield(**kwargs)
