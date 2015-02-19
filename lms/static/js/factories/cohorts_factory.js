;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/collections/cohort','js/groups/models/cohort_settings',
            'js/discussion_topics/models/topics', 'js/discussion_topics/collections/topics'
        ],
        function($) {

            return function(contentGroups, studioGroupConfigurationsUrl) {

                var cohorts = new edx.groups.CohortCollection(),
                    cohortSettings = new edx.groups.CohortSettingsModel(),
                    discussionTopics = new edx.discussions.DiscussionTopicsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('ajax_url');
                cohortSettings.url = cohortManagementElement.data('cohort_settings_url');
                discussionTopics.url = cohortManagementElement.data('discussion_topics_url');

                var cohortsView = new edx.groups.CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: cohortSettings,
                    context: {
                        discussionTopicsModel: discussionTopics,
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        studioAdvancedSettingsUrl: cohortManagementElement.data('advanced-settings-url'),
                        studioGroupConfigurationsUrl: studioGroupConfigurationsUrl
                    }
                });

                var discussionTopicsView = new edx.discussions.DiscussionTopicsView({
                    el: cohortManagementElement,
                    model: discussionTopics,
                    //discussionsTopics: discussionsTopics ,
                    //cohortSettings: cohortSettings,
                    context: {
                        discussionsTopicsUrl: cohortManagementElement.data('discussion_topics_url')
                    }
                });

                cohorts.fetch().done(function() {
                    cohortSettings.fetch().done(function() {
                        discussionTopics.fetch().done(function() {
                            cohortsView.render();
                            //discussionTopicsView.render();
                        });
                    });
                });
            };
    });
}).call(this, define || RequireJS.define);