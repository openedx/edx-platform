from django.contrib import admin

from .models import CompetencyAssessmentRecord


class CompetencyAssessmentRecordModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)


admin.site.register(CompetencyAssessmentRecord, CompetencyAssessmentRecordModelAdmin)
