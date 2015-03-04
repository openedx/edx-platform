;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/course_cohort_settings',
            'js/groups/models/cohort_discussions'],
        function($) {

            return function(contentGroups, studioGroupConfigurationsUrl) {

                var cohorts = new edx.groups.CohortCollection(),
                    courseCohortSettings = new edx.groups.CourseCohortSettingsModel(),
                    discussionTopics = new edx.groups.DiscussionTopicsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('cohorts_url');
                courseCohortSettings.url = cohortManagementElement.data('course_cohort_settings_url');
                discussionTopics.url = cohortManagementElement.data('discussion-topics-url');
                
                var cohortsView = new edx.groups.CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: courseCohortSettings,
                    context: {
                        discussionTopicsModel: discussionTopics,
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        studioAdvancedSettingsUrl: cohortManagementElement.data('advanced-settings-url'),
                        studioGroupConfigurationsUrl: studioGroupConfigurationsUrl
                    }
                });

                cohorts.fetch().done(function() {
                    courseCohortSettings.fetch().done(function() {
                        discussionTopics.fetch().done(function() {
                            cohortsView.render();
                        });
                    });
                });
            };
    });
}).call(this, define || RequireJS.define);

