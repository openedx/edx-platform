;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/collections/cohort', 'js/groups/models/cohort_settings'],
        function($) {

            return function(contentGroups, studioGroupConfigurationsUrl) {

                var cohorts = new edx.groups.CohortCollection(),
                    cohortSettings = new edx.groups.CohortSettingsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('ajax_url');
                cohortSettings.url = cohortManagementElement.data('cohort_settings_url');

                var cohortsView = new edx.groups.CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: cohortSettings,
                    context: {
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        studioAdvancedSettingsUrl: cohortManagementElement.data('advanced-settings-url'),
                        studioGroupConfigurationsUrl: studioGroupConfigurationsUrl
                    }
                });
                cohorts.fetch().done(function() {
                    cohortSettings.fetch().done(function() {
                        cohortsView.render();
                    })
                });
            };
    });
}).call(this, define || RequireJS.define);