define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/views/account_settings_fields',
        'js/student_account/models/user_account_model',
        'js/student_account/models/user_preferences_model',
        'js/student_profile/views/learner_profile_view'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel,
                AccountPreferencesModel, LearnerProfileView) {
        'use strict';

        describe("edx.user.LearnerProfileView", function (options) {

            var createLearnerProfileView = function (ownProfile, accountPrivacy, profileIsPublic) {

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set(Helpers.USER_ACCOUNTS_DATA);
                accountSettingsModel.set({'profile_is_public': profileIsPublic});

                var accountPreferencesModel = new AccountPreferencesModel();
                accountPreferencesModel.set({account_privacy: accountPrivacy});

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
                        ['all_users', 'Full Profile'],
                        ['private', 'Limited Profile']
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
                    usernameFieldView,
                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-map-marker',
                        placeholderValue: 'Add country',
                        valueAttribute: "country",
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    }),

                    new FieldViews.DropdownFieldView({
                        model: accountSettingsModel,
                        required: false,
                        editable: editable,
                        showMessages: false,
                        iconName: 'fa-comment fa-flip-horizontal',
                        placeholderValue: 'Add language',
                        valueAttribute: "language",
                        options: Helpers.FIELD_OPTIONS,
                        helpMessage: ''
                    })
                ];

                var sectionTwoFieldViews = [
                    new FieldViews.TextareaFieldView({
                        model: accountSettingsModel,
                        editable: editable,
                        showMessages: false,
                        title: 'About me',
                        placeholderValue: "Tell other edX learners a little about yourself, where you're from, what your interests are, why you joined edX, what you hope to learn...",
                        valueAttribute: "bio",
                        helpMessage: ''
                    })
                ];

                return new LearnerProfileView(
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

            };

            beforeEach(function () {
                setFixtures('<div class="wrapper-profile"><div class="ui-loading-indicator"><p><span class="spin"><i class="icon fa fa-refresh"></i></span> <span class="copy">Loading</span></p></div><div class="ui-loading-error is-hidden"><i class="fa fa-exclamation-triangle message-error" aria-hidden=true></i><span class="copy">An error occurred. Please reload the page.</span></div></div>');
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
            });

            var expectElementContainsField = function(element, view) {
                var $element = $(element);
                var fieldTitle = $element.find('.u-field-title').text().trim();

                if (!_.isUndefined(view.options.title)) {
                    if (view.modelValue()) {
                        expect(fieldTitle).toBe(view.options.title);
                    } else {
                        expect(fieldTitle).toBe('+ ' + view.options.title);
                    }
                }

                if ('fieldValue' in view) {
                    expect(view.model.get(view.options.valueAttribute)).toBeTruthy();

                    if (view.fieldValue()) {
                        expect(view.fieldValue()).toBe(view.modelValue());

                    } else if ('optionForValue' in view) {
                        expect($($element.find('.u-field-value')[0]).text()).toBe(view.optionForValue(view.modelValue())[1]);

                    }else {
                        expect($($element.find('.u-field-value')[0]).text()).toBe(view.modelValue());
                    }
                } else {
                    throw new Error('Unexpected field type: ' + view.fieldType);
                }
            };

            var expectProfilePrivacyFieldTobeRendered = function(learnerProfileView, othersProfile) {

                var accountPrivacyElement = learnerProfileView.$('.wrapper-profile-field-account-privacy');
                var privacyFieldElement = $(accountPrivacyElement).find('.u-field');

                if (othersProfile) {
                    expect(privacyFieldElement.length).toBe(0);
                } else {
                    expect(privacyFieldElement.length).toBe(1);
                    expectElementContainsField(privacyFieldElement, learnerProfileView.options.accountPrivacyFieldView)
                }
            };

            var expectSectionOneTobeRendered = function(learnerProfileView) {

                var sectionOneFieldElements = $(learnerProfileView.$('.wrapper-profile-section-one')).find('.u-field');

                expect(sectionOneFieldElements.length).toBe(learnerProfileView.options.sectionOneFieldViews.length);

                _.each(sectionOneFieldElements, function (sectionFieldElement, fieldIndex) {
                    expectElementContainsField(sectionFieldElement, learnerProfileView.options.sectionOneFieldViews[fieldIndex]);
                });
            };

            var expectSectionTwoTobeRendered = function(learnerProfileView) {

                var sectionTwoElement = learnerProfileView.$('.wrapper-profile-section-two');
                var sectionTwoFieldElements = $(sectionTwoElement).find('.u-field');

                expect(sectionTwoFieldElements.length).toBe(learnerProfileView.options.sectionTwoFieldViews.length);

                 _.each(sectionTwoFieldElements, function (sectionFieldElement, fieldIndex) {
                    expectElementContainsField(sectionFieldElement, learnerProfileView.options.sectionTwoFieldViews[fieldIndex]);
                });
            };
            var expectProfileSectionsAndFieldsToBeRendered = function (learnerProfileView, othersProfile) {
                expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);
                expectSectionOneTobeRendered(learnerProfileView);
                expectSectionTwoTobeRendered(learnerProfileView);
            };

            var expectLimitedProfileSectionsAndFieldsToBeRendered = function (learnerProfileView, othersProfile) {
                expectProfilePrivacyFieldTobeRendered(learnerProfileView, othersProfile);

                var sectionOneFieldElements = $(learnerProfileView.$('.wrapper-profile-section-one')).find('.u-field');

                expect(sectionOneFieldElements.length).toBe(1);
                _.each(sectionOneFieldElements, function (sectionFieldElement, fieldIndex) {
                    expectElementContainsField(sectionFieldElement, learnerProfileView.options.sectionOneFieldViews[fieldIndex]);
                });

                expect($('.profile-private--message').text()).toBe('This edX learner is not currently sharing their profile details.')
            };

            it("shows loading error correctly", function() {

                var learnerProfileView = createLearnerProfileView(false, 'all_users');

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();
                learnerProfileView.showLoadingError();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, true);
            });

            it("renders all fields as expected for self with full access", function() {

                var learnerProfileView = createLearnerProfileView(true, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                expectProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders all fields as expected for self with limited access", function() {

                var learnerProfileView = createLearnerProfileView(true, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView);
            });

            it("renders the fields as expected for others with full access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'all_users', true);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                expectProfileSectionsAndFieldsToBeRendered(learnerProfileView, true)
            });

            it("renders the fields as expected for others with limited access", function() {

                var learnerProfileView = createLearnerProfileView(false, 'private', false);

                Helpers.expectLoadingIndicatorIsVisible(learnerProfileView, true);
                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);

                learnerProfileView.render();

                Helpers.expectLoadingErrorIsVisible(learnerProfileView, false);
                expectLimitedProfileSectionsAndFieldsToBeRendered(learnerProfileView, true);
            });

        });
    });
