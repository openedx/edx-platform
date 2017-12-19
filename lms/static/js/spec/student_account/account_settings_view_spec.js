define(['backbone',
    'jquery',
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/spec/student_account/helpers',
    'js/views/fields',
    'js/student_account/models/user_account_model',
    'js/student_account/views/account_settings_view'
],
    function(Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, FieldViews, UserAccountModel,
              AccountSettingsView) {
        'use strict';

        describe('edx.user.AccountSettingsView', function() {
            var createAccountSettingsView = function() {
                var model = new UserAccountModel();
                model.set(Helpers.createAccountSettingsData());

                var aboutSectionsData = [
                    {
                        title: 'Basic Account Information',
                        messageType: 'info',
                        message: 'Your profile settings are managed by Test Enterprise. ' +
                        'Contact your administrator or <a href="https://support.edx.org/">edX Support</a> for help.',
                        fields: [
                            {
                                view: new FieldViews.ReadonlyFieldView({
                                    model: model,
                                    title: 'Username',
                                    valueAttribute: 'username'
                                })
                            },
                            {
                                view: new FieldViews.TextFieldView({
                                    model: model,
                                    title: 'Full Name',
                                    valueAttribute: 'name'
                                })
                            }
                        ]
                    },
                    {
                        title: 'Additional Information',
                        fields: [
                            {
                                view: new FieldViews.DropdownFieldView({
                                    model: model,
                                    title: 'Education Completed',
                                    valueAttribute: 'level_of_education',
                                    options: Helpers.FIELD_OPTIONS
                                })
                            }
                        ]
                    }
                ];

                var accountSettingsView = new AccountSettingsView({
                    el: $('.wrapper-account-settings'),
                    model: model,
                    tabSections: {
                        aboutTabSections: aboutSectionsData
                    }
                });

                return accountSettingsView;
            };

            beforeEach(function() {
                setFixtures('<div class="wrapper-account-settings"></div>');
            });

            it('shows loading error correctly', function() {
                var accountSettingsView = createAccountSettingsView();

                accountSettingsView.render();
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);

                accountSettingsView.showLoadingError();
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, true);
            });

            it('renders all fields as expected', function() {
                var accountSettingsView = createAccountSettingsView();

                accountSettingsView.render();
                Helpers.expectLoadingErrorIsVisible(accountSettingsView, false);
                Helpers.expectSettingsSectionsAndFieldsToBeRendered(accountSettingsView);
            });
        });
    });
