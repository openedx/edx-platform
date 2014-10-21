define(['js/common_helpers/template_helpers', 'js/student_account/views/AccessView'],
    function(TemplateHelpers) {
        describe("edx.student.account.AccessView", function() {
            'use strict';

            var view = null,
                ajaxSuccess = true;

            beforeEach(function() {
                var mainFixture = "<div id='login-and-registration-container'class='login-register'data-initial-mode='${initial_mode}'data-third-party-auth-providers='${third_party_auth_providers}'/>";

                setFixtures(mainFixture);
                TemplateHelpers.installTemplate("templates/student_account/access");
                TemplateHelpers.installTemplate("templates/student_account/login");

                // Stub AJAX calls to return success / failure
                spyOn($, "ajax").andCallFake(function() {
                    return $.Deferred(function(defer) {
                        if (ajaxSuccess) {
                            defer.resolve();
                        } else {
                            defer.reject();
                        }
                    }).promise();
                });

                view = new edx.student.account.AccessView({
                    mode: 'login',
                    thirdPartyAuth: false
                });
            });

            it("initially displays the correct form", function() {
                expect(view.subview.login.$form).not.toHaveClass('hidden');
                expect($("#register-form")).toHaveClass('hidden');
                expect($("#password-reset-wrapper")).toBeEmpty();
            });

            it("toggles between the login and registration forms", function() {
                // TODO
            });

            it("displays the reset password form", function() {
                // TODO
            });
        });
    }
);
