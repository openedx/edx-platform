define(['js/common_helpers/template_helpers', 'js/student_account/views/PasswordResetView'],
    function(TemplateHelpers) {
        describe("edx.student.account.PasswordResetView", function() {
            'use strict';

            beforeEach(function() {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate("templates/student_account/password_reset");
            });

            it("allows the user to request a new password", function() {
                // TODO
            });

            it("validates the email field", function() {
                // TODO
            });

            it("displays password reset errors", function() {
                // TODO
            });

            it("displays an error if the server could not be contacted", function() {
                // TODO
            });
        });
    }
);
