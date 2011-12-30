from django.contrib import admin
from django import forms
from django.utils.translation import ugettext as _
from models import Article, Revision, Permission, ArticleAttachment

class RevisionInline(admin.TabularInline):
    model = Revision
    extra = 1

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('article', '__unicode__', 'revision_date', 'revision_user', 'revision_text')
    search_fields = ('article', 'counter')

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('article', '__unicode__', 'uploaded_on', 'uploaded_by')

class ArticleAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get("slug").startswith('_'):
            raise forms.ValidationError(_('Slug cannot start with _ character.'
                                          'Reserved for internal use.'))
        if not self.instance.pk:
            parent = cleaned_data.get("parent")
            slug = cleaned_data.get("slug")
            if Article.objects.filter(slug__exact=slug, parent__exact=parent):
                raise forms.ValidationError(_('Article slug and parent must be '
                                              'unique together.'))
        return cleaned_data
    class Meta:
        model = Article

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'slug', 'modified_on', 'parent')
    search_fields = ('slug',)
    prepopulated_fields = {'slug': ('title',) }
    inlines = [RevisionInline]
    form = ArticleAdminForm
    save_on_top = True
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'current_revision':
            # Try to determine the id of the article being edited
            id = request.path.split('/')
            import re
            if len(id) > 0 and re.match(r"\d+", id[-2]):
                kwargs["queryset"] = Revision.objects.filter(article=id[-2])
                return db_field.formfield(**kwargs)
            else:
                db_field.editable = False
                return db_field.formfield(**kwargs)
        return super(ArticleAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class PermissionAdmin(admin.ModelAdmin):
    search_fields = ('article', 'counter')

admin.site.register(Article, ArticleAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(ArticleAttachment, AttachmentAdmin)