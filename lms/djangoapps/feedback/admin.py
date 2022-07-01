from django.contrib import admin
from .models import Feedback
admin.site.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('email', 'instance_code', 'unit_title', 'category_id', 'content')