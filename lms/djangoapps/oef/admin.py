from django.contrib import admin

from lms.djangoapps.oef.models import OptionLevel, TopicQuestion, Option, OefSurvey, \
    Instruction, OrganizationOefScore, OrganizationOefUpdatePrompt


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


class OrganizationOefScoreAdmin(admin.ModelAdmin):
    list_display = ('finish_date', 'org', 'user')
    search_fields = ('org__label', 'user__username')


class OrganizationOefUpdatePromptAdmin(admin.ModelAdmin):
    list_display = ('latest_finish_date', 'year', 'responsible_user', 'org')
    search_fields = ('org__label', 'responsible_user__username')

admin.site.register(OptionLevel)
admin.site.register(Option)
admin.site.register(Instruction)
admin.site.register(TopicQuestion, TopicQuestionAdmin)
admin.site.register(OefSurvey, OefSurveyAdmin)
admin.site.register(OrganizationOefScore, OrganizationOefScoreAdmin)
admin.site.register(OrganizationOefUpdatePrompt, OrganizationOefUpdatePromptAdmin)
