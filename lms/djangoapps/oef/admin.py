from django.contrib import admin

from lms.djangoapps.oef.models import OptionPriority, TopicQuestion, Option, OefSurvey


class OptionPriorityAdmin(admin.ModelAdmin):
    model = OptionPriority


class OptionInlineAdmin(admin.TabularInline):
    model = Option


class TopicQuestionInlineAdmin(admin.TabularInline):
    inlines = (OptionInlineAdmin,)
    model = TopicQuestion

class TopicQuestionAdmin(admin.ModelAdmin):
    inlines = (OptionInlineAdmin,)
    model = TopicQuestion


class OefSurveyAdmin(admin.ModelAdmin):
    inlines = (TopicQuestionInlineAdmin,)


admin.site.register(OptionPriority)
admin.site.register(Option)
admin.site.register(TopicQuestion, TopicQuestionAdmin)
admin.site.register(OefSurvey, OefSurveyAdmin)