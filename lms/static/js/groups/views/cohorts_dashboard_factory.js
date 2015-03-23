;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/course_cohort_settings',
            'js/groups/models/cohort_discussions'],
        function($) {

            return function(contentGroups, studioGroupConfigurationsUrl) {

                var cohorts = new edx.groups.CohortCollection(),
                    courseCohortSettings = new edx.groups.CourseCohortSettingsModel(),
                    discussionTopicsSettings = new edx.groups.DiscussionTopicsSettingsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('cohorts_url');
                courseCohortSettings.url = cohortManagementElement.data('course_cohort_settings_url');
                discussionTopicsSettings.url = cohortManagementElement.data('discussion-topics-url');
                
                var cohortsView = new edx.groups.CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: courseCohortSettings,
                    context: {
                        discussionTopicsSettingsModel: discussionTopicsSettings,
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        studioGroupConfigurationsUrl: studioGroupConfigurationsUrl
                    }
                });

                cohorts.fetch().done(function() {
                    courseCohortSettings.fetch().done(function() {
                        discussionTopicsSettings.fetch().done(function() {
                            cohortsView.render();
                        });
                    });
                });
            };
    });
}).call(this, define || RequireJS.define);

