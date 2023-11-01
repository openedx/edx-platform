from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.db.models import Count, F
from openedx.features.genplus_features.genplus.constants import GenUserRoles

from openedx.features.genplus_features.genplus.models import ClassStudents, Student, School


class MoreThanOneClassFilter(SimpleListFilter):
    title = "More than one class."  # a label for our filter
    parameter_name = ""  # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; we have two:
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        # This is where you process parameters selected by use via filter options:
        if self.value() == "yes":
            student_ids = ClassStudents.objects.values('student').annotate(count=Count('gen_class', distinct=True)).filter(count__gt=1).values_list('student', flat=True)
            return queryset.filter(id__in=student_ids)
        return queryset.all()


class DifferentActiveClassFilter(SimpleListFilter):
    title = "Different Active class."  # a label for our filter
    parameter_name = "different_active_class"  # you can put anything here

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            student_ids = Student.objects.filter(active_class__in=F('classes')).values_list('id', flat=True)
            return queryset.exclude(id__in=student_ids)
        return queryset.all()


class WithoutClassStudents(SimpleListFilter):
    title = "Students Without Class"  # a label for our filter
    parameter_name = "filter_students_without_class"  # you can put anything here

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(gen_user__role=GenUserRoles.STUDENT, gen_user__student__active_class__isnull=True)
        return queryset.all()


class SchoolFilter(SimpleListFilter):
    title = "School"  # a label for our filter
    parameter_name = "filter_students_by_school"  # you can put anything here

    def lookups(self, request, model_admin):
        return [
            (school.guid, school.name) for school in School.objects.filter(is_active=True)
        ]

    def queryset(self, request, queryset):
        guid = self.value()
        if guid:
            return queryset.filter(gen_user__role=GenUserRoles.STUDENT, gen_user__school_id=guid)

        return queryset.all()
