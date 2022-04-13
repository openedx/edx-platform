""" Django admin pages for save_for_later app """

from django.contrib import admin

from lms.djangoapps.save_for_later.models import SavedCourse, SavedProgram


class SavedCourseAdmin(admin.ModelAdmin):
    """
    Admin for the Saved Course table.
    """

    list_display = ['email', 'course_id', 'email_sent_count', 'reminder_email_sent']

    search_fields = ['email', 'course_id']


class SavedProgramAdmin(admin.ModelAdmin):
    """
    Admin for the Saved Program table.
    """

    list_display = ['email', 'program_uuid', 'email_sent_count', 'reminder_email_sent']

    search_fields = ['email', 'program_uuid']


admin.site.register(SavedCourse, SavedCourseAdmin)
admin.site.register(SavedProgram, SavedProgramAdmin)
