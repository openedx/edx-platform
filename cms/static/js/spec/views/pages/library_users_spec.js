define([
    "jquery", "js/common_helpers/ajax_helpers", "js/spec_helpers/view_helpers",
    "js/factories/manage_users_lib", "js/views/utils/view_utils"
],
function ($, AjaxHelpers, ViewHelpers, ManageUsersFactory, ViewUtils) {
    "use strict";
    describe("Library Instructor Access Page", function () {
        var mockHTML = readFixtures('mock/mock-manage-users-lib.underscore');

        beforeEach(function () {
            ViewHelpers.installMockAnalytics();
            appendSetFixtures(mockHTML);
            ManageUsersFactory(
                "Mock Library",
                ["honor@example.com", "audit@example.com", "staff@example.com"],
                "dummy_change_role_url"
            );
        });

        afterEach(function () {
            ViewHelpers.removeMockAnalytics();
        });

        it("can give a user permission to use the library", function () {
            var requests = AjaxHelpers.requests(this);
            var reloadSpy = spyOn(ViewUtils, 'reload');
            $('.create-user-button').click();
            expect($('.wrapper-create-user')).toHaveClass('is-shown');
            $('.user-email-input').val('other@example.com');
            $('.form-create.create-user .action-primary').click();
            AjaxHelpers.expectJsonRequest(requests, 'POST', 'dummy_change_role_url', {role: 'library_user'});
            AjaxHelpers.respondWithJson(requests, {'result': 'ok'});
            expect(reloadSpy).toHaveBeenCalled();
        });

        it("can cancel adding a user to the library", function () {
            $('.create-user-button').click();
            $('.form-create.create-user .action-secondary').click();
            expect($('.wrapper-create-user')).not.toHaveClass('is-shown');
        });

        it("displays an error when the required field is blank", function () {
            var requests = AjaxHelpers.requests(this);
            $('.create-user-button').click();
            $('.user-email-input').val('');
            var errorPromptSelector = '.wrapper-prompt.is-shown .prompt.error';
            expect($(errorPromptSelector).length).toEqual(0);
            $('.form-create.create-user .action-primary').click();
            expect($(errorPromptSelector).length).toEqual(1);
            expect($(errorPromptSelector)).toContainText('You must enter a valid email address');
            expect(requests.length).toEqual(0);
        });

        it("displays an error when the user has already been added", function () {
            var requests = AjaxHelpers.requests(this);
            $('.create-user-button').click();
            $('.user-email-input').val('honor@example.com');
            var warningPromptSelector = '.wrapper-prompt.is-shown .prompt.warning';
            expect($(warningPromptSelector).length).toEqual(0);
            $('.form-create.create-user .action-primary').click();
            expect($(warningPromptSelector).length).toEqual(1);
            expect($(warningPromptSelector)).toContainText('Already a library team member');
            expect(requests.length).toEqual(0);
        });


        it("can remove a user's permission to access the library", function () {
            var requests = AjaxHelpers.requests(this);
            var reloadSpy = spyOn(ViewUtils, 'reload');
            $('.user-item[data-email="honor@example.com"] .action-delete .delete').click();
            expect($('.wrapper-prompt.is-shown .prompt.warning').length).toEqual(1);
            $('.wrapper-prompt.is-shown .action-primary').click();
            AjaxHelpers.expectJsonRequest(requests, 'DELETE', 'dummy_change_role_url', {role: null});
            AjaxHelpers.respondWithJson(requests, {'result': 'ok'});
            expect(reloadSpy).toHaveBeenCalled();
        });
    });
});
