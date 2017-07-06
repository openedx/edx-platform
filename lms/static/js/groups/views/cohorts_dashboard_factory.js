;(function (define, undefined) {
    'use strict';
    define(['jquery', 'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/course_cohort_settings',
            'js/groups/models/cohort_discussions', 'js/groups/models/content_group'],
        function($, CohortsView, CohortCollection, CourseCohortSettingsModel, DiscussionTopicsSettingsModel, ContentGroupModel) {

            return function(contentGroups, studioGroupConfigurationsUrl) {
                var contentGroupModels = $.map(contentGroups, function(group) {
                    return new ContentGroupModel({
                        id: group.id,
                        name: group.name,
                        user_partition_id: group.user_partition_id
                    });
                });

                var cohorts = new CohortCollection(),
                    courseCohortSettings = new CourseCohortSettingsModel(),
                    discussionTopicsSettings = new DiscussionTopicsSettingsModel();

                var cohortManagementElement = $('.cohort-management');

                cohorts.url = cohortManagementElement.data('cohorts_url');
                courseCohortSettings.url = cohortManagementElement.data('course_cohort_settings_url');
                discussionTopicsSettings.url = cohortManagementElement.data('discussion-topics-url');
                
                var cohortsView = new CohortsView({
                    el: cohortManagementElement,
                    model: cohorts,
                    contentGroups: contentGroupModels,
                    cohortSettings: courseCohortSettings,
                    context: {
                        discussionTopicsSettingsModel: discussionTopicsSettings,
                        uploadCohortsCsvUrl: cohortManagementElement.data('upload_cohorts_csv_url'),
                        verifiedTrackCohortingUrl: cohortManagementElement.data('verified_track_cohorting_url'),
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

