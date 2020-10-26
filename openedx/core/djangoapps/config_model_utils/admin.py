"""
Convenience classes for defining StackedConfigModel Admin pages.
"""

from django import forms

from opaque_keys.edx.keys import CourseKey

from config_models.admin import ConfigurationModelAdmin


class CourseOverviewField(forms.ModelChoiceField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        return super(CourseOverviewField, self).to_python(CourseKey.from_string(value))


class StackedConfigModelAdminForm(forms.ModelForm):
    class Meta:
        field_classes = {
            'course': CourseOverviewField
        }


class StackedConfigModelAdmin(ConfigurationModelAdmin):
    """
    A specialized ConfigurationModel ModelAdmin for StackedConfigModels.
    """
    form = StackedConfigModelAdminForm

    def get_fields(self, request, obj=None):
        fields = super(StackedConfigModelAdmin, self).get_fields(request, obj)
        return list(self.model.KEY_FIELDS) + [field for field in fields if field not in self.model.KEY_FIELDS]

    def get_displayable_field_names(self):
        """
        Return all field names, excluding reverse foreign key relationships.
        """
        names = super(StackedConfigModelAdmin, self).get_displayable_field_names()
        fixed_names = ['id', 'change_date', 'changed_by'] + list(self.model.KEY_FIELDS)
        return fixed_names + [name for name in names if name not in fixed_names]
