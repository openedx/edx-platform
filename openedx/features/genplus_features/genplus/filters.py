from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.db.models import Count, F
from openedx.features.genplus_features.genplus.models import ClassStudents, Student


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
            return queryset.exclude(id__in=student_ids, active_class__isnull=True)
        return queryset.all()
