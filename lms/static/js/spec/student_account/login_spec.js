define(['js/common_helpers/template_helpers', 'js/student_account/views/LoginView'],
    function(TemplateHelpers) {
        describe("edx.student.account.LoginView", function() {
            'use strict';

            beforeEach(function() {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate("templates/student_account/login");
            });

            it("logs the user in", function() {
                // TODO
            });

            it("displays third party auth login buttons", function() {
                // TODO
            });

            it("validates the email field", function() {
                // TODO
            });

            it("validates the password field", function() {
                // TODO
            });

            it("displays login errors", function() {
                // TODO
            });

            it("displays an error if the form definition could not be loaded", function() {
                // TODO
            });

            it("displays an error if the server could not be contacted while logging in", function() {
                // TODO
            });

            it("allows the user to navigate to the password assistance form", function() {
                // TODO
            });

            it("enrolls the student into the right location and forwards them properly", function() {
                // TODO
            });
        });
    }
);
