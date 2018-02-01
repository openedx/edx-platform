from django.contrib import admin

from lms.djangoapps.oef.models import OptionLevel, TopicQuestion, Option, OefSurvey, Instruction


class OptionPriorityAdmin(admin.ModelAdmin):
    model = OptionLevel


class OptionInlineAdmin(admin.TabularInline):
    model = Option


class TopicQuestionInlineAdmin(admin.TabularInline):
    inlines = (OptionInlineAdmin,)
    model = TopicQuestion
    ordering = ("order_number",)


class TopicQuestionAdmin(admin.ModelAdmin):
    inlines = (OptionInlineAdmin,)
    model = TopicQuestion
    ordering = ("order_number",)


class OefSurveyAdmin(admin.ModelAdmin):
    inlines = (TopicQuestionInlineAdmin,)


admin.site.register(OptionLevel)
admin.site.register(Option)
admin.site.register(Instruction)
admin.site.register(TopicQuestion, TopicQuestionAdmin)
admin.site.register(OefSurvey, OefSurveyAdmin)
