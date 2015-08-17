define([
    'jquery', 'annotator_1.2.9', 'common/js/spec_helpers/ajax_helpers', 'js/edxnotes/views/visibility_decorator',
    'js/edxnotes/views/toggle_notes_factory', 'js/spec/edxnotes/helpers',
    'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function(
    $, Annotator, AjaxHelpers, VisibilityDecorator, ToggleNotesFactory, Helpers,
    customMatchers
) {
    'use strict';
    describe('EdxNotes ToggleNotesFactory', function() {
        var params = {
            endpoint: '/test_endpoint',
            user: 'a user',
            usageId : 'an usage',
            courseId: 'a course',
            token: Helpers.makeToken(),
            tokenUrl: '/test_token_url'
        };

        beforeEach(function() {
            customMatchers(this);
            loadFixtures(
                'js/fixtures/edxnotes/edxnotes_wrapper.html',
                'js/fixtures/edxnotes/toggle_notes.html'
            );
            VisibilityDecorator.factory(
                document.getElementById('edx-notes-wrapper-123'), params, true
            );
            VisibilityDecorator.factory(
                document.getElementById('edx-notes-wrapper-456'), params, true
            );
            this.toggleNotes = ToggleNotesFactory(true, '/test_url');
            this.button = $('.action-toggle-notes');
            this.label = this.button.find('.utility-control-label');
            this.toggleMessage = $('.action-toggle-message');
            spyOn(this.toggleNotes, 'toggleHandler').andCallThrough();
        });

        afterEach(function () {
            VisibilityDecorator._setVisibility(null);
            _.invoke(Annotator._instances, 'destroy');
            $('.annotator-notice').remove();
        });

        it('can toggle notes', function() {
            var requests = AjaxHelpers.requests(this);

            expect(this.button).not.toHaveClass('is-disabled');
            expect(this.label).toContainText('Hide notes');
            expect(this.button).toHaveClass('is-active');
            expect(this.button).toHaveAttr('aria-pressed', 'true');
            expect(this.toggleMessage).not.toHaveClass('is-fleeting');
            expect(this.toggleMessage).toContainText('Notes visible');

            this.button.click();
            expect(this.label).toContainText('Show notes');
            expect(this.button).not.toHaveClass('is-active');
            expect(this.toggleMessage).toHaveClass('is-fleeting');
            expect(this.toggleMessage).toContainText('Notes hidden');
            expect(Annotator._instances).toHaveLength(0);

            AjaxHelpers.expectJsonRequest(requests, 'PUT', '/test_url', {
                'visibility': false
            });
            AjaxHelpers.respondWithJson(requests, {});

            this.button.click();
            expect(this.label).toContainText('Hide notes');
            expect(this.button).toHaveClass('is-active');
            expect(this.toggleMessage).toHaveClass('is-fleeting');
            expect(this.toggleMessage).toContainText('Notes visible');
            expect(Annotator._instances).toHaveLength(2);

            AjaxHelpers.expectJsonRequest(requests, 'PUT', '/test_url', {
                'visibility': true
            });
            AjaxHelpers.respondWithJson(requests, {});
        });

        it('can handle errors', function() {
            var requests = AjaxHelpers.requests(this),
                errorContainer = $('.annotator-notice');

            this.button.click();
            AjaxHelpers.respondWithError(requests);
            expect(errorContainer).toContainText(
                "An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page."
            );
            expect(errorContainer).toBeVisible();
            expect(errorContainer).toHaveClass('annotator-notice-show');
            expect(errorContainer).toHaveClass('annotator-notice-error');

            this.button.click();
            AjaxHelpers.respondWithJson(requests, {});
            expect(errorContainer).not.toHaveClass('annotator-notice-show');
        });

        it('toggles notes when CTRL + SHIFT + [ keydown on document', function () {
            // Character '[' has keyCode 219
            $(document).trigger($.Event('keydown', {keyCode: 219, ctrlKey: true, shiftKey: true}));
            expect(this.toggleNotes.toggleHandler).toHaveBeenCalled();
        });
    });
});
