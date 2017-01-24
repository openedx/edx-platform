"""
Basic admin screens to search and edit InstructorTasks.

This will mostly involve searching by course_id or task_id and manually failing
a task.

"""
from django.contrib import admin
from .models import InstructorTask


class InstructorTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_id',
        'task_type',
        'course_id',
        'username',
        'email',
        'created',
        'updated',
    ]
    list_filter = ['task_type', 'task_state']
    search_fields = [
        'task_id', 'course_id', 'requester__email', 'requester__username'
    ]
    raw_id_fields = ['requester']  # avoid trying to make a select dropdown

    def email(self, task):
        return task.requester.email
    email.admin_order_field = 'requester__email'

    def username(self, task):
        return task.requester.username
    email.admin_order_field = 'requester__username'

admin.site.register(InstructorTask, InstructorTaskAdmin)
