define(['js/common_helpers/template_helpers', 'js/common_helpers/ajax_helpers', 'js/student_account/views/AccessView'],
    function(TemplateHelpers, AjaxHelpers) {
        describe('edx.student.account.AccessView', function() {
            'use strict';

            var requests = null,
                view = null,
                LOGIN_URL = '/user_api/v1/account/login_session/',
                LOGIN_REQUESTS_INDEX = 0,
                REGISTER_URL = '/user_api/v1/account/registration/',
                REGISTER_REQUESTS_INDEX = 1,
                FORM_DESCRIPTION = {
                    "method": "post",
                    "submit_url": "/submit",
                    "fields": [
                        {
                            "name": "email",
                            "label": "Email",
                            "defaultValue": "",
                            "type": "text",
                            "required": true,
                            "placeholder": "xsy@edx.org",
                            "instructions": "Enter your email here.",
                            "restrictions": {},
                        },
                        {
                            "name": "username",
                            "label": "Username",
                            "defaultValue": "",
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

            var ajaxAssertAndRespond = function(url, requestIndex) {
                // Verify that the client contacts the server
                AjaxHelpers.expectJsonRequest(requests, 'GET', url, null, requestIndex);

                // Simulate a response from the server containing
                // a form description
                AjaxHelpers.respondWithJson(requests, FORM_DESCRIPTION);
            }

            var assertForms = function(visible, hidden) {
                expect($(visible)).not.toHaveClass('hidden');
                expect($(hidden)).toHaveClass('hidden');
                expect($('#password-reset-wrapper')).toBeEmpty();
            };

            var selectForm = function(changeEvent) {
                // Load form corresponding to the change event
                view.toggleForm(changeEvent);

                if ($(changeEvent.currentTarget).val() === 'register') {
                    ajaxAssertAndRespond(REGISTER_URL, REGISTER_REQUESTS_INDEX);
                    assertForms('#register-form', '#login-form');
                } else {
                    ajaxAssertAndRespond(LOGIN_URL, LOGIN_REQUESTS_INDEX);
                    assertForms('#login-form', '#register-form');
                };
            };

            beforeEach(function() {
                setFixtures("<div id='login-and-registration-container'></div>");
                TemplateHelpers.installTemplate('templates/student_account/access');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(this);

                view = new edx.student.account.AccessView({
                    mode: 'login',
                    thirdPartyAuth: {
                        currentProvider: null,
                        providers: []
                    }
                });

                // Simulate a response from the server containing
                // a form description
                AjaxHelpers.respondWithJson(requests, FORM_DESCRIPTION);
            });

            it("initially displays the correct form", function() {
                assertForms('#login-form', '#register-form');
            });

            it("toggles between the login and registration forms", function() {
                // Create fake change events used to control form toggling
                var registerChangeEvent = $.Event('change', {currentTarget: $('#register-option')}),
                    loginChangeEvent = $.Event('change', {currentTarget: $('#login-option')});

                // Simulate selection of the registration form
                selectForm(registerChangeEvent);

                // Simulate selection of the login form
                selectForm(loginChangeEvent);
            });

            it("displays the reset password form", function() {
                view.resetPassword();
                expect($('#password-reset-wrapper')).not.toBeEmpty();
            });
        });
    }
);
