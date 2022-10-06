from django.contrib import admin
from .models import Article, Reflection, ReflectionAnswer, ArticleRating, MediaType, Gtcs, ArticleViewLog
from django.urls import reverse
from django.utils.safestring import mark_safe


class ReflectionAdminInline(admin.TabularInline):
    model = Reflection


class ArticleAdmin(admin.ModelAdmin):
    inlines = (ReflectionAdminInline,)
    filter_horizontal = ('skills', 'gtcs', 'media_types')
    list_display = ('title', 'reflections', 'time', 'favorites_count', 'rating_average')

    def reflections(self, obj):
        url = reverse('admin:genplus_teach_reflection_changelist')
        return mark_safe('<a href="%s?article__id__exact=%s">View Reflections</a>' % (url, obj.pk))


class ReflectionAdmin(admin.ModelAdmin):
    list_filter = ('article', )


admin.site.register(Article, ArticleAdmin)
admin.site.register(Reflection, ReflectionAdmin)
admin.site.register(ReflectionAnswer)
admin.site.register(ArticleRating)
admin.site.register(Gtcs)
admin.site.register(MediaType)
admin.site.register(ArticleViewLog)
