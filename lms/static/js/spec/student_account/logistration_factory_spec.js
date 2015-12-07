;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'backbone',
            'common/js/spec_helpers/template_helpers',
            'common/js/spec_helpers/ajax_helpers',
            'js/student_account/logistration_factory'
        ],
        function($, _, Backbone, TemplateHelpers, AjaxHelpers, LogistrationFactory) {

        describe('Logistration Factory', function() {
            var FORM_DESCRIPTION = {
                    method: 'post',
                    submit_url: '/submit',
                    fields: [
                        {
                            name: 'email',
                            label: 'Email',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            placeholder: 'xsy@edx.org',
                            instructions: 'Enter your email here.',
                            restrictions: {}
                        },
                        {
                            name: 'username',
                            label: 'Username',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            placeholder: 'Xsy',
                            instructions: 'Enter your username here.',
                            restrictions: {
                                max_length: 200
                            }
                        }
                    ]
                };

            var initializeLogistrationFactory = function(that, mode, nextUrl, finishAuthUrl) {
                var options = {
                    initial_mode: mode,
                    third_party_auth: {
                        currentProvider: null,
                        providers: [],
                        secondaryProviders: [{name: 'provider'}],
                        finishAuthUrl: finishAuthUrl
                    },
                    login_redirect_url: nextUrl, // undefined for default
                    platform_name: 'edX',
                    login_form_desc: FORM_DESCRIPTION,
                    registration_form_desc: FORM_DESCRIPTION,
                    password_reset_form_desc: FORM_DESCRIPTION
                };

                // Initialize the logistration Factory
                LogistrationFactory(options);
            };

            var assertForms = function(visibleForm, hiddenFormsList) {
                expect($(visibleForm)).not.toHaveClass('hidden');

                _.each(hiddenFormsList, function (hiddenForm) {
                    expect($(hiddenForm)).toHaveClass('hidden');
                }, this);
            };

            beforeEach(function() {
                setFixtures('<div id="login-and-registration-container" class="login-register" />');
                TemplateHelpers.installTemplate('templates/student_account/access');
                TemplateHelpers.installTemplate('templates/student_account/form_field');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/password_reset')
            });

            afterEach(function() {
                Backbone.history.stop();
            });

            it('can initially render the login form', function() {
                var hiddenFormsList;

                initializeLogistrationFactory(this, 'login');

                /* Verify that only login form is expanded, and that the
                /* all other logistration forms are collapsed.
                 */
                hiddenFormsList = [
                    '#register-form',
                    '#password-reset-form'
                ];
                assertForms('#login-form', hiddenFormsList);
            });

            it('can initially render the registration form', function() {
                var hiddenFormsList;

                initializeLogistrationFactory(this, 'register');

                /* Verify that only registration form is expanded, and that the
                /* all other logistration forms are collapsed.
                 */
                hiddenFormsList = [
                    '#login-form',
                    '#password-reset-form'
                ];
                assertForms('#register-form', hiddenFormsList);
            });

            it('can initially render the password reset form', function() {
                var hiddenFormsList;

                initializeLogistrationFactory(this, 'reset');

                /* Verify that only password reset form is expanded, and that the
                /* all other logistration forms are collapsed.
                 */
                hiddenFormsList = [
                    '#login-form',
                    '#register-form'
                ];
                assertForms('#password-reset-form', hiddenFormsList);
            });
        });
    });
}).call(this, define || RequireJS.define);
