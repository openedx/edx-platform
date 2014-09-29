define(['js/student_profile/profile'],
    function() {
        describe("edx.student.profile.ProfileModel", function() {
            'use strict';

            var profile = null;

            beforeEach(function() {
                profile = new edx.student.profile.ProfileModel();
            });

            it("validates the full name field", function() {
                // Full name cannot be blank
                profile.set("fullName", "");
                var errors = profile.validate(profile.attributes);
                expect(errors).toEqual({
                    fullName: "Full name cannot be blank"
                });

                // Fill in the name and expect that the model is valid
                profile.set("fullName", "Bob");
                errors = profile.validate(profile.attributes);
                expect(errors).toBe(undefined);
            });
        });

        describe("edx.student.profile.PreferencesModel", function() {
            var preferences = null;

            beforeEach(function() {
                preferences = new edx.student.profile.PreferencesModel();
            });

            it("validates the language field", function() {
                // Language cannot be blank
                preferences.set("language", "");
                var errors = preferences.validate(preferences.attributes);
                expect(errors).toEqual({
                    language: "Language cannot be blank"
                });

                // Fill in the language and expect that the model is valid
                preferences.set("language", "eo");
                errors = preferences.validate(preferences.attributes);
                expect(errors).toBe(undefined);
            });
        });

        describe("edx.student.profile.ProfileView", function() {
            var view = null,
                ajaxSuccess = true;

            var updateProfile = function(fields) {
                view.profileModel.set(fields);
                view.clearStatus();
                view.profileModel.save();
            };

            var updatePreferences = function(fields) {
                view.preferencesModel.set(fields);
                view.clearStatus();
                view.preferencesModel.save();
            };

            var assertAjax = function(url, method, data) {
                expect($.ajax).toHaveBeenCalled();
                var ajaxArgs = $.ajax.mostRecentCall.args[0];
                expect(ajaxArgs.url).toEqual(url);
                expect(ajaxArgs.type).toEqual(method);
                expect(ajaxArgs.data).toEqual(data)
                expect(ajaxArgs.headers.hasOwnProperty("X-CSRFToken")).toBe(true);
            };

            var assertSubmitStatus = function(success, expectedStatus) {
                if (!success) {
                    expect(view.$submitStatus).toHaveClass("error");
                } else {
                    expect(view.$submitStatus).not.toHaveClass("error");
                }
                expect(view.$submitStatus.text()).toEqual(expectedStatus);
            };

            var assertValidationError = function(expectedError, selection) {
                if (expectedError === null) {
                    expect(selection).not.toHaveClass("validation-error");
                    expect(selection.text()).toEqual("");
                } else {
                    expect(selection).toHaveClass("validation-error");
                    expect(selection.text()).toEqual(expectedError);
                }
            };

            beforeEach(function() {
                var profileFixture = readFixtures("templates/student_profile/profile.underscore"),
                    languageFixture = readFixtures("templates/student_profile/languages.underscore");

                setFixtures("<div id=\"profile-tpl\">" + profileFixture + "</div>");
                appendSetFixtures("<div id=\"languages-tpl\">" + languageFixture + "</div>");

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

                var json = {
                    preferredLanguage: {code: 'eo', name: 'Dummy language'},
                    languages: [{code: 'eo', name: 'Dummy language'}]
                };
                spyOn($, "getJSON").andCallFake(function() {
                    return $.Deferred(function(defer) {
                        if (ajaxSuccess) {
                            defer.resolveWith(this, [json]);
                        } else {
                            defer.reject();
                        }
                    }).promise();
                });

                // Stub location.reload() to prevent test suite from reloading repeatedly
                spyOn(edx.student.profile, "reloadPage").andCallFake(function() {
                    return true;
                });

                view = new edx.student.profile.ProfileView().render();
            });

            it("updates the student profile", function() {
                updateProfile({fullName: "John Smith"});
                assertAjax("", "PUT", {fullName: "John Smith"});
                assertSubmitStatus(true, "Saved");
            });

            it("updates the student preferences", function() {
                updatePreferences({language: "eo"});
                assertAjax("preferences", "PUT", {language: "eo"});
                assertSubmitStatus(true, "Saved");
            });

            it("displays full name validation errors", function() {
                // Blank name should display a validation error
                updateProfile({fullName: ""});
                assertValidationError("Full name cannot be blank", view.$nameStatus);

                // If we fix the problem and resubmit, the error should go away
                updateProfile({fullName: "John Smith"});
                assertValidationError(null, view.$nameStatus);
            });

            it("displays language validation errors", function() {
                // Blank language should display a validation error
                updatePreferences({language: ""});
                assertValidationError("Language cannot be blank", view.$languageStatus);

                // If we fix the problem and resubmit, the error should go away
                updatePreferences({language: "eo"});
                assertValidationError(null, view.$languageStatus);
            });

            it("displays an error if the sync fails", function() {
                // If we get an error status on the AJAX request, display an error
                ajaxSuccess = false;
                updateProfile({fullName: "John Smith"});
                assertSubmitStatus(false, "The data could not be saved.");

                // If we try again and succeed, the error should go away
                ajaxSuccess = true;
                updateProfile({fullName: "John Smith"});
                assertSubmitStatus(true, "Saved");
            });
        });
    }
);
