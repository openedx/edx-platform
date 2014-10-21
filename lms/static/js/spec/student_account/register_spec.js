define(['js/common_helpers/template_helpers', 'js/student_account/views/RegisterView'],
    function(TemplateHelpers) {
        describe("edx.student.account.RegisterView", function() {
            'use strict';

            beforeEach(function() {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate("templates/student_account/register");
            });

            it("registers a new user", function() {
                // TODO
            });

            it("displays third party auth registration buttons", function() {
                // TODO
            });

            it("validates form fields", function() {
                // TODO
            });

            it("displays registration errors", function() {
                // TODO
            });

            it("displays an error if the form definition could not be loaded", function() {
                // TODO
            });

            it("displays an error if the server could not be contacted while registering", function() {
                // TODO
            });
        });
    }
);
