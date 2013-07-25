from django.contrib import admin

from bulk_email.models import CourseEmail, Optout

admin.site.register(Optout)


class CourseEmailAdmin(admin.ModelAdmin):
    readonly_fields = ('sender',)

admin.site.register(CourseEmail, CourseEmailAdmin)
