define(['js/student_account/account'],
    function() {
        describe("edx.student.account.AccountModel", function() {
            'use strict';

            var account = null;

            var assertValid = function(fields, isValid, expectedErrors) {
                account.set(fields);
                var errors = account.validate(account.attributes);

                if (isValid) {
                    expect(errors).toBe(undefined);
                } else {
                    expect(errors).toEqual(expectedErrors);
                }
            };

            var EXPECTED_ERRORS = {
                email: {
                    email: "Please enter a valid email address"
                },
                password: {
                    password: "Please enter a valid password"
                }
            };

            beforeEach(function() {
                account = new edx.student.account.AccountModel();
                account.set({
                    email: "bob@example.com",
                    password: "password"
                });
            });

            it("accepts valid email addresses", function() {
                assertValid({email: "bob@example.com"}, true);
                assertValid({email: "bob+smith@example.com"}, true);
                assertValid({email: "bob+smith@example.com"}, true);
                assertValid({email: "bob+smith@example.com"}, true);
                assertValid({email: "bob@test.example.com"}, true);
                assertValid({email: "bob@test-example.com"}, true);
            });

            it("rejects blank email addresses", function() {
                assertValid({email: ""}, false, EXPECTED_ERRORS.email);
                assertValid({email: "      "}, false, EXPECTED_ERRORS.email);
            });

            it("rejects invalid email addresses", function() {
                assertValid({email: "bob"}, false, EXPECTED_ERRORS.email);
                assertValid({email: "bob@example"}, false, EXPECTED_ERRORS.email);
                assertValid({email: "@"}, false, EXPECTED_ERRORS.email);
                assertValid({email: "@example.com"}, false, EXPECTED_ERRORS.email);

                // The server will reject emails with non-ASCII unicode
                // Technically these are valid email addresses, but the email validator
                // in Django 1.4 will reject them anyway, so we should too.
                assertValid({email: "fŕáńḱ@example.com"}, false, EXPECTED_ERRORS.email);
                assertValid({email: "frank@éxáḿṕĺé.com"}, false, EXPECTED_ERRORS.email);
            });

            it("rejects a long email address", function() {
                // Construct an email exactly one character longer than the maximum length
                var longEmail = new Array(account.EMAIL_MAX_LENGTH - 10).join("e") + "@example.com";
                assertValid({email: longEmail}, false, EXPECTED_ERRORS.email);
            });

            it("accepts a valid password", function() {
                assertValid({password: "password-test123"}, true, EXPECTED_ERRORS.password);
            });

            it("rejects a short password", function() {
                assertValid({password: ""}, false, EXPECTED_ERRORS.password);
                assertValid({password: "a"}, false, EXPECTED_ERRORS.password);
                assertValid({password: "aa"}, true, EXPECTED_ERRORS.password);
            });

            it("rejects a long password", function() {
                // Construct a password exactly one character longer than the maximum length
                var longPassword = new Array(account.PASSWORD_MAX_LENGTH + 2).join("a");
                assertValid({password: longPassword}, false, EXPECTED_ERRORS.password);
            });
        });


        describe("edx.student.account.AccountView", function() {
            var view = null,
                ajaxSuccess = true;

            var requestEmailChange = function(email, password) {
                var fakeEvent = {preventDefault: function() {}};
                view.model.set({
                    email: email,
                    password: password
                });
                view.submit(fakeEvent);
            };

            var requestPasswordChange = function() {
                var fakeEvent = {preventDefault: function() {}};
                view.click(fakeEvent);
            };

            var assertAjax = function(url, method, data) {
                expect($.ajax).toHaveBeenCalled();
                var ajaxArgs = $.ajax.calls.mostRecent().args[0];
                expect(ajaxArgs.url).toEqual(url);
                expect(ajaxArgs.type).toEqual(method);
                expect(ajaxArgs.data).toEqual(data);
                expect(ajaxArgs.headers.hasOwnProperty("X-CSRFToken")).toBe(true);
            };

            var assertStatus = function(selection, success, errorClass, expectedStatus) {
                if (!success) {
                    expect(selection).toHaveClass(errorClass);
                } else {
                    expect(selection).not.toHaveClass(errorClass);
                }
                expect(selection.text()).toEqual(expectedStatus);
            };

            beforeEach(function() {
                var fixture = readFixtures("templates/student_account/account.underscore");
                setFixtures("<div id=\"account-tpl\">" + fixture + "</div>");

                view = new edx.student.account.AccountView().render();

                // Stub Ajax calls to return success/failure
                spyOn($, "ajax").and.callFake(function() {
                    return $.Deferred(function(defer) {
                        if (ajaxSuccess) {
                            defer.resolve();
                        } else {
                            defer.reject();
                        }
                    }).promise();
                });
            });

            it("requests an email address change", function() {
                requestEmailChange("bob@example.com", "password");
                assertAjax("email", "POST", {
                    email: "bob@example.com",
                    password: "password"
                });
                assertStatus(view.$requestStatus, true, "error", "Please check your email to confirm the change");
            });

            it("displays email validation errors", function() {
                // Invalid email should display an error
                requestEmailChange("invalid", "password");
                assertStatus(view.$emailStatus, false, "validation-error", "Please enter a valid email address");

                // Once the error is fixed, the status should return to normal
                requestEmailChange("bob@example.com", "password");
                assertStatus(view.$emailStatus, true, "validation-error", "");
            });

            it("displays an invalid password error", function() {
                // Password cannot be empty
                requestEmailChange("bob@example.com", "");
                assertStatus(view.$passwordStatus, false, "validation-error", "Please enter a valid password");

                // Once the error is fixed, the status should return to normal
                requestEmailChange("bob@example.com", "password");
                assertStatus(view.$passwordStatus, true, "validation-error", "");
            });

            it("displays server errors", function() {
                // Simulate an error from the server
                ajaxSuccess = false;
                requestEmailChange("bob@example.com", "password");
                assertStatus(view.$requestStatus, false, "error", "The data could not be saved.");

                // On retry, it should succeed
                ajaxSuccess = true;
                requestEmailChange("bob@example.com", "password");
                assertStatus(view.$requestStatus, true, "error", "Please check your email to confirm the change");
            });

            it("requests a password reset", function() {
                requestPasswordChange();
                assertAjax("password", "POST", {});
                assertStatus(view.$passwordResetStatus, true, "error", "Password reset email sent. Follow the link in the email to change your password.");
            });

            it("displays an error message if a password reset email could not be sent", function() {
                // Simulate an error from the server
                ajaxSuccess = false;
                requestPasswordChange();
                assertStatus(view.$passwordResetStatus, false, "error", "We weren't able to send you a password reset email.");

                // Retry, this time simulating success
                ajaxSuccess = true;
                requestPasswordChange();
                assertStatus(view.$passwordResetStatus, true, "error", "Password reset email sent. Follow the link in the email to change your password.");
            });
        });
    }
);
