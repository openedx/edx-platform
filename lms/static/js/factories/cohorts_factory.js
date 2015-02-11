;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/course_cohort_settings'],
        function($) {

            return function(contentGroups, studioGroupConfigurationsUrl) {

                var cohorts = new edx.groups.CohortCollection(),
                    courseCohortSettings = new edx.groups.CourseCohortSettingsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('cohorts_url');
                courseCohortSettings.url = cohortManagementElement.data('course_cohort_settings_url');

                var cohortsView = new edx.groups.CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: courseCohortSettings,
                    context: {
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        studioAdvancedSettingsUrl: cohortManagementElement.data('advanced-settings-url'),
                        studioGroupConfigurationsUrl: studioGroupConfigurationsUrl
                    }
                });
                cohorts.fetch().done(function() {
                    courseCohortSettings.fetch().done(function() {
                        cohortsView.render();
                    })
                });
            };
    });
}).call(this, define || RequireJS.define);

