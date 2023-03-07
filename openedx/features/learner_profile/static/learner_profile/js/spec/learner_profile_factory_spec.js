define(
    [
        'backbone', 'jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'learner_profile/js/spec_helpers/helpers',
        'js/views/fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'learner_profile/js/views/learner_profile_view',
        'learner_profile/js/views/learner_profile_fields',
        'learner_profile/js/learner_profile_factory',
        'js/views/message_banner'
    ],
    function(Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, LearnerProfileHelpers, FieldViews,
        UserAccountModel, UserPreferencesModel, LearnerProfileView, LearnerProfileFields, LearnerProfilePage) {
        'use strict';

        describe('edx.user.LearnerProfileFactory', function() {
            var createProfilePage;

            beforeEach(function() {
                loadFixtures('learner_profile/fixtures/learner_profile.html');
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            createProfilePage = function(ownProfile, options) {
                return new LearnerProfilePage({
                    accounts_api_url: Helpers.USER_ACCOUNTS_API_URL,
                    preferences_api_url: Helpers.USER_PREFERENCES_API_URL,
                    badges_api_url: Helpers.BADGES_API_URL,
                    own_profile: ownProfile,
                    account_settings_page_url: Helpers.USER_ACCOUNTS_API_URL,
                    country_options: Helpers.FIELD_OPTIONS,
                    language_options: Helpers.FIELD_OPTIONS,
                    has_preferences_access: true,
                    profile_image_max_bytes: Helpers.IMAGE_MAX_BYTES,
                    profile_image_min_bytes: Helpers.IMAGE_MIN_BYTES,
                    profile_image_upload_url: Helpers.IMAGE_UPLOAD_API_URL,
                    profile_image_remove_url: Helpers.IMAGE_REMOVE_API_URL,
                    default_visibility: 'all_users',
                    platform_name: 'edX',
                    find_courses_url: '/courses/',
                    account_settings_data: Helpers.createAccountSettingsData(options),
                    preferences_data: Helpers.createUserPreferencesData()
                });
            };

            it('renders the full profile for a user', function() {
                var context,
                    learnerProfileView;
                AjaxHelpers.requests(this);
                context = createProfilePage(true);
                learnerProfileView = context.learnerProfileView;

                // sets the profile for full view.
                context.accountPreferencesModel.set({account_privacy: 'all_users'});
                LearnerProfileHelpers.expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, false);
            });

            it("renders the limited profile for undefined 'year_of_birth'", function() {
                var context = createProfilePage(true, {year_of_birth: '', requires_parental_consent: true}),
                    learnerProfileView = context.learnerProfileView;

                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("doesn't show the mode toggle if badges are disabled", function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: false}),
                    tabbedView = context.learnerProfileView.tabbedView,
                    learnerProfileView = context.learnerProfileView;

                LearnerProfileHelpers.expectTabbedViewToBeUndefined(requests, tabbedView);
                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
            });

            it("doesn't show the mode toggle if badges fail to fetch", function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: false}),
                    tabbedView = context.learnerProfileView.tabbedView,
                    learnerProfileView = context.learnerProfileView;

                LearnerProfileHelpers.expectTabbedViewToBeUndefined(requests, tabbedView);
                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
            });

            it('renders the mode toggle if there are badges', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    tabbedView = context.learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.firstPageBadges);

                LearnerProfileHelpers.expectTabbedViewToBeShown(tabbedView);
            });

            it('renders the mode toggle if badges enabled but none exist', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    tabbedView = context.learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.emptyBadges);

                LearnerProfileHelpers.expectTabbedViewToBeShown(tabbedView);
            });

            it('displays the badges when the accomplishments toggle is selected', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    learnerProfileView = context.learnerProfileView,
                    tabbedView = learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.secondPageBadges);

                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
                tabbedView.$el.find('[data-url="accomplishments"]').click();
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 10, false);
                tabbedView.$el.find('[data-url="about_me"]').click();
                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
            });

            it('displays a placeholder on the last page of badges', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    learnerProfileView = context.learnerProfileView,
                    tabbedView = learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.thirdPageBadges);

                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
                tabbedView.$el.find('[data-url="accomplishments"]').click();
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 10, true);
                tabbedView.$el.find('[data-url="about_me"]').click();
                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
            });

            it('displays a placeholder when the accomplishments toggle is selected and no badges exist', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    learnerProfileView = context.learnerProfileView,
                    tabbedView = learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.emptyBadges);

                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
                tabbedView.$el.find('[data-url="accomplishments"]').click();
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 0, true);
                tabbedView.$el.find('[data-url="about_me"]').click();
                LearnerProfileHelpers.expectBadgesHidden(learnerProfileView);
            });

            it('shows a paginated list of badges', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    learnerProfileView = context.learnerProfileView,
                    tabbedView = learnerProfileView.tabbedView;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.firstPageBadges);

                tabbedView.$el.find('[data-url="accomplishments"]').click();
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 10, false);
                LearnerProfileHelpers.expectPage(learnerProfileView, LearnerProfileHelpers.firstPageBadges);
            });

            it('allows forward and backward navigation of badges', function() {
                var requests = AjaxHelpers.requests(this),
                    context = createProfilePage(true, {accomplishments_shared: true}),
                    learnerProfileView = context.learnerProfileView,
                    tabbedView = learnerProfileView.tabbedView,
                    badgeListContainer = context.badgeListContainer;

                AjaxHelpers.expectRequest(requests, 'POST', '/event');
                AjaxHelpers.respondWithError(requests, 404);
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.firstPageBadges);

                tabbedView.$el.find('[data-url="accomplishments"]').click();

                badgeListContainer.$el.find('.next-page-link').click();
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.secondPageBadges);
                LearnerProfileHelpers.expectPage(learnerProfileView, LearnerProfileHelpers.secondPageBadges);

                badgeListContainer.$el.find('.next-page-link').click();
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.thirdPageBadges);
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 10, true);
                LearnerProfileHelpers.expectPage(learnerProfileView, LearnerProfileHelpers.thirdPageBadges);

                badgeListContainer.$el.find('.previous-page-link').click();
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.secondPageBadges);
                LearnerProfileHelpers.expectPage(learnerProfileView, LearnerProfileHelpers.secondPageBadges);
                LearnerProfileHelpers.expectBadgesDisplayed(learnerProfileView, 10, false);

                badgeListContainer.$el.find('.previous-page-link').click();
                AjaxHelpers.respondWithJson(requests, LearnerProfileHelpers.firstPageBadges);
                LearnerProfileHelpers.expectPage(learnerProfileView, LearnerProfileHelpers.firstPageBadges);
            });


            it('renders the limited profile for under 13 users', function() {
                var context = createProfilePage(
                    true,
                    {year_of_birth: new Date().getFullYear() - 10, requires_parental_consent: true}
                );
                var learnerProfileView = context.learnerProfileView;
                LearnerProfileHelpers.expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });
        });
    });
