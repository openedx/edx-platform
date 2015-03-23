define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/learner_profile_view'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel,
                AccountPreferencesModel, LearnerProfileView) {
        'use strict';

        describe("edx.user.LearnerProfileView", function (options) {

            var createLearnerProfileView = function (ownProfile) {

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set(Helpers.USER_ACCOUNTS_DATA);

                var accountPreferencesModel = new AccountPreferencesModel();
                accountPreferencesModel.url = Helpers.USER_PREFERENCES_API_URL;

                var editable = ownProfile ? 'toggle' : 'never';

                var accountPrivacyFieldView = new FieldViews.AccountPrivacyFieldView({
                    model: accountPreferencesModel,
                    required: true,
                    editable: 'always',
                    showMessages: false,
                    title: 'edX learners can see my:',
                    valueAttribute: "account_privacy",
                    options: [
                        ['private', gettext('Limited Profile')],
                        ['all_users', gettext('Full Profile')]
                    ],
                    helpMessage: '',
                    accountSettingsPageUrl: '/account/settings/'
                });

                var usernameFieldView = new FieldViews.ReadonlyFieldView({
                        model: accountSettingsModel,
                        valueAttribute: "username",
                        helpMessage: ""
                });

                var sectionOneFieldViews = [
                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-map-marker',
                        placeholderValue: 'Add country',
                        valueAttribute: "country",
                        options: options['country_options'],
                        helpMessage: ''
                    }),

                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-comment fa-flip-horizontal',
                        placeholderValue: gettext('Add language'),
                        valueAttribute: "language",
                        options: options['language_options'],
                        helpMessage: ''
                    })
                ];

                var sectionTwoFieldViews = [
                    new FieldViews.TextareaFieldView({
                        model: accountSettingsModel,
                        editable: editable,
                        showMessages: false,
                        title: gettext('About me'),
                        placeholderValue: gettext("Tell other edX learners a little about yourself, where you're from, what your interests are, why you joined edX, what you hope to learn..."),
                        valueAttribute: "bio",
                        helpMessage: ''
                    })
                ];

                var learnerProfileView = new LearnerProfileView(
                    {
                        el: $('.wrapper-profile'),
                        own_profile: ownProfile,
                        has_preferences_access: true,
                        accountSettingsModel: accountSettingsModel,
                        preferencesModel: accountPreferencesModel,
                        accountPrivacyFieldView: accountPrivacyFieldView,
                        usernameFieldView: usernameFieldView,
                        sectionOneFieldViews: sectionOneFieldViews,
                        sectionTwoFieldViews: sectionTwoFieldViews
                    });

                return learnerProfileView;
            };

            beforeEach(function () {
                setFixtures('<div class="wrapper-profile"></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
            });

            it("shows loading error correctly", function() {

                var accountSettingsView = createLearnerProfileView();

                accountSettingsView.render();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                accountSettingsView.showLoadingError();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);
            });

            it("renders all fields as expected", function() {

                var accountSettingsView = createLearnerProfileView();

                accountSettingsView.render();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, true);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsButNotFieldsToBeRendered(accountSettingsView);

                accountSettingsView.renderFields();
                Helpers.expectLoadingIndicatorIsVisible(accountSettingsView, false);
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView)
            });

        });
    });
