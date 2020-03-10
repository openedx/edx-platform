import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import UCSDCustomRegistration


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(UCSDCustomRegistration)
class UCSDCustomRegistrationAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('user', 'gender_nb', 'ethnicity', 'age', 'education', 'howheard')
    actions = ["export_as_csv"]
