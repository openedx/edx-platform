from django.contrib import admin
from .models import Article, Reflection, ReflectionAnswer, ArticleRating, MediaType, Gtcs, ArticleViewLog,\
    Quote, HelpGuideType, HelpGuide, AlertBarEntry, HelpGuideRating, PortfolioEntry
from django.urls import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe


class ReflectionAdminInline(admin.TabularInline):
    model = Reflection


class ArticleAdmin(admin.ModelAdmin):
    inlines = (ReflectionAdminInline,)
    filter_horizontal = ('skills', 'gtcs', 'media_types')
    list_display = ('title', 'reflections', 'time', 'favorites_count', 'rating_average', 'is_featured', 'is_archived',
                    'is_draft', 'academic_year')
    list_filter = ('is_archived', 'is_draft', 'academic_year', 'is_featured')
    actions = ['mark_as_featured', ]

    def reflections(self, obj):
        url = reverse('admin:genplus_teach_reflection_changelist')
        return mark_safe('<a href="%s?article__id__exact=%s">View Reflections</a>' % (url, obj.pk))

    def mark_as_featured(modeladmin, request, queryset):
        if queryset.count() > 1:
            messages.add_message(request, messages.ERROR, 'You cannot mark more than one class as featured.')
        else:
            # marking the other article as non-featured
            Article.objects.filter(is_featured=True).update(is_featured=False)
            queryset.update(is_featured=True)
            messages.add_message(request, messages.SUCCESS, 'Marked as featured.')


class ReflectionAdmin(admin.ModelAdmin):
    list_filter = ('article',)


class QuoteAdmin(admin.ModelAdmin):
    actions = ['mark_as_quote_of_the_week', ]
    list_display = ['text', 'is_current']

    def mark_as_quote_of_the_week(modeladmin, request, queryset):
        if queryset.count() > 1:
            messages.add_message(request, messages.ERROR, 'You cannot mark more than one quote.')
        else:
            # marking the other article as non-featured
            Quote.objects.filter(is_current=True).update(is_current=False)
            queryset.update(is_current=True)
            messages.add_message(request, messages.SUCCESS, 'Marked as quote of the week.')


class HelpGuideAdmin(admin.ModelAdmin):
    filter_horizontal = ('media_types', )


admin.site.register(Article, ArticleAdmin)
admin.site.register(Reflection, ReflectionAdmin)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(ReflectionAnswer)
admin.site.register(ArticleRating)
admin.site.register(Gtcs)
admin.site.register(MediaType)
admin.site.register(ArticleViewLog)
admin.site.register(HelpGuideType)
admin.site.register(HelpGuide, HelpGuideAdmin)
admin.site.register(HelpGuideRating)
admin.site.register(AlertBarEntry)
admin.site.register(PortfolioEntry)
