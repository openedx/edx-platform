define(['jquery', 'js/factories/login', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/components/utils/view_utils'],
function($, LoginFactory, AjaxHelpers, ViewUtils) {
    'use strict';
    describe("Studio Login Page", function() {
        var submitButton;

        beforeEach(function() {
            loadFixtures('mock/login.underscore');
            var login_factory = new LoginFactory("/home/");
            submitButton = $('#submit');
        });

        it('disable the submit button once it is clicked', function() {
            spyOn(ViewUtils, 'redirect').and.callFake(function(){});
            var requests = AjaxHelpers.requests(this);
            expect(submitButton).not.toHaveClass('is-disabled');
            submitButton.click();
            AjaxHelpers.respondWithJson(requests, {'success': true});
            expect(submitButton).toHaveClass('is-disabled');
        });

        it('It will not disable the submit button if there are errors in ajax request', function() {
            var requests = AjaxHelpers.requests(this);
            expect(submitButton).not.toHaveClass('is-disabled');
            submitButton.click();
            expect(submitButton).toHaveClass('is-disabled');
            AjaxHelpers.respondWithError(requests, {});
            expect(submitButton).not.toHaveClass('is-disabled');
        });
    });
});
