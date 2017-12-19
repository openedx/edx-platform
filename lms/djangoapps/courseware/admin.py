from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin

from courseware import models

admin.site.register(models.DynamicUpgradeDeadlineConfiguration, ConfigurationModelAdmin)
admin.site.register(models.OfflineComputedGrade)
admin.site.register(models.OfflineComputedGradeLog)
admin.site.register(models.CourseDynamicUpgradeDeadlineConfiguration, KeyedConfigurationModelAdmin)
admin.site.register(models.OrgDynamicUpgradeDeadlineConfiguration, KeyedConfigurationModelAdmin)
admin.site.register(models.StudentModule)
