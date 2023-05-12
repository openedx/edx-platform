/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(define, undefined) {
    'use strict';

    define(['jquery', 'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/course_cohort_settings',
        'js/groups/models/content_group'],
    function($, CohortsView, CohortCollection, CourseCohortSettingsModel, ContentGroupModel) {
        return function(contentGroups, studioGroupConfigurationsUrl) {
            // eslint-disable-next-line no-var
            var contentGroupModels = $.map(contentGroups, function(group) {
                return new ContentGroupModel({
                    id: group.id,
                    name: group.name,
                    user_partition_id: group.user_partition_id
                });
            });

            // eslint-disable-next-line no-var
            var cohorts = new CohortCollection(),
                courseCohortSettings = new CourseCohortSettingsModel(),
                $cohortManagementElement = $('.cohort-management');

            cohorts.url = $cohortManagementElement.data('cohorts_url');
            courseCohortSettings.url = $cohortManagementElement.data('course_cohort_settings_url');

            // eslint-disable-next-line no-var
            var cohortsView = new CohortsView({
                el: $cohortManagementElement,
                model: cohorts,
                contentGroups: contentGroupModels,
                cohortSettings: courseCohortSettings,
                context: {
                    uploadCohortsCsvUrl: $cohortManagementElement.data('upload_cohorts_csv_url'),
                    studioGroupConfigurationsUrl: studioGroupConfigurationsUrl,
                    isCcxEnabled: $cohortManagementElement.data('is_ccx_enabled')
                }
            });

            cohorts.fetch().done(function() {
                courseCohortSettings.fetch().done(function() {
                    cohortsView.render();
                });
            });
        };
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
