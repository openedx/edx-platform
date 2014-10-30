define(['js/common_helpers/template_helpers', 'js/student_account/views/AccessView'],
    function(TemplateHelpers, AccessView) {
        describe('edx.student.account.AccessView', function() {
            'use strict';

            var view = null,
                ajaxSuccess = true;

            var assertForms = function(visible, hidden) {
                expect($(visible)).not.toHaveClass('hidden');
                expect($(hidden)).toHaveClass('hidden');
                expect($('#password-reset-wrapper')).toBeEmpty();
            };

            beforeEach(function() {
                setFixtures("<div id='login-and-registration-container'></div>");
                TemplateHelpers.installTemplate('templates/student_account/access');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');

                // Used to populate forms
                var form_description = {
                    "method": "post",
                    "submit_url": "/submit",
                    "fields": [
                        {
                            "name": "email",
                            "label": "Email",
                            "default": "",
                            "type": "text",
                            "required": true,
                            "placeholder": "xsy@edx.org",
                            "instructions": "Enter your email here.",
                            "restrictions": {},
                        },
                        {
                            "name": "username",
                            "label": "Username",
                            "default": "",
                            "type": "text",
                            "required": true,
                            "placeholder": "Xsy",
                            "instructions": "Enter your username here.",
                            "restrictions": {
                                "max_length": 200
                            }
                        }
                    ]
                };

                // Stub AJAX calls and force them to return a form description
                spyOn($, 'ajax').andCallFake(function() {
                    return $.Deferred(function(defer) {
                        if (ajaxSuccess) {
                            defer.resolveWith(this, [form_description]);
                        } else {
                            defer.reject();
                        }
                    }).promise();
                });

                view = new edx.student.account.AccessView({
                    mode: 'login',
                    thirdPartyAuth: {
                        currentProvider: null,
                        providers: []
                    }
                });
            });

            it("initially displays the correct form", function() {
                assertForms($('#login-form'), $('#register-form'));
            });

            it("toggles between the login and registration forms", function() {
                var registerChangeEvent = $.Event('change', {currentTarget: $('#register-option')}),
                    loginChangeEvent = $.Event('change', {currentTarget: $('#login-option')});

                // Simulate selection of the registration form
                view.toggleForm(registerChangeEvent)
                assertForms($('#register-form'), $('#login-form'));

                // Simulate selection of the login form
                view.toggleForm(loginChangeEvent)
                assertForms($('#login-form'), $('#register-form'));
            });

            it("displays the reset password form", function() {
                view.resetPassword();
                expect($('#password-reset-wrapper')).not.toBeEmpty();
            });
        });
    }
);
