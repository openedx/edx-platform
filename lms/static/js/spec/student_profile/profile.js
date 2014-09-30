describe("edx.student.ProfileModel", function() {

    var profile = null;

    beforeEach(function() {
        profile = new edx.student.profile.ProfileModel();
    });

    it("validates the full name field", function() {
        // Full name cannot be blank
        profile.set('fullName', '');
        var errors = profile.validate(profile.attributes);
        expect(errors).toEqual({
            fullName: "Full name cannot be blank"
        });

        // Fill in the name and expect that the model is valid
        profile.set('fullName', 'Bob');
        errors = profile.validate(profile.attributes);
        expect(errors).toBe(undefined);
    });

});

describe("edx.student.ProfileView", function() {
    var view = null;
    var ajaxSuccess = true;

    var updateProfile = function(fields) {
        var fakeEvent = {preventDefault: function() {}};
        view.model.set(fields);
        view.submit(fakeEvent);
    };

    var assertAjax = function(url, method, data) {
        expect($.ajax).toHaveBeenCalled();
        var ajaxArgs = $.ajax.mostRecentCall.args[0];
        expect(ajaxArgs.url).toEqual(url);
        expect(ajaxArgs.type).toEqual(method);
        expect(ajaxArgs.data).toEqual(data)
        expect(ajaxArgs.headers.hasOwnProperty('X-CSRFToken')).toBe(true);
    };

    var assertSubmitStatus = function(success, expectedStatus) {
        if (!success) {
            expect(view.$submitStatus).toHaveClass('error');
        }
        else {
            expect(view.$submitStatus).not.toHaveClass('error');
        }
        expect(view.$submitStatus.text()).toEqual(expectedStatus);
    };

    var assertValidationError = function(expectedError) {
        if (expectedError === null) {
            expect(view.$nameStatus).not.toHaveClass('validation-error');
            expect(view.$nameStatus.text()).toEqual('');
        }
        else {
            expect(view.$nameStatus).toHaveClass('validation-error');
            expect(view.$nameStatus.text()).toEqual(expectedError);
        }
    };

    beforeEach(function() {
        var fixture = readFixtures('js/fixtures/student_profile/profile.underscore');
        setFixtures('<div id="profile-tpl">' + fixture + '</div>');

        view = new edx.student.profile.ProfileView().render();

        // Stub AJAX calls to return success / failure
        spyOn($, 'ajax').andCallFake(function() {
            return $.Deferred(function(defer) {
                if (ajaxSuccess) { defer.resolve(); }
                else { defer.reject(); }
            }).promise();
        });
    });

    it("updates the student profile", function() {
        updateProfile({ fullName: 'John Smith' });
        assertAjax('/', 'PUT', { fullName: 'John Smith' });
        assertSubmitStatus(true, "Saved");
    });

    it("displays validation errors", function() {
        // Blank name should display a validation error
        updateProfile({ fullName: '' });
        assertValidationError("Full name cannot be blank");

        // If we fix the problem and resubmit, the error should go away
        updateProfile({ fullName: 'John Smith' });
        assertValidationError(null);
    });

    it("displays an error if the sync fails", function() {
        // If we get an error status on the AJAX request, display an error
        ajaxSuccess = false;
        updateProfile({ fullName: 'John Smith' });
        assertSubmitStatus(false, 'The data could not be saved.');

        // If we try again and succeed, the error should go away
        ajaxSuccess = true;
        updateProfile({ fullName: 'John Smith' });
        assertSubmitStatus(true, 'Saved');
    });
});