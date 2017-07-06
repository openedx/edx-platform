define([
    'jquery', 'underscore', 'annotator_1.2.9', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'js/edxnotes/views/notes_visibility_factory', 'js/spec/edxnotes/helpers'
], function(
    $, _, Annotator, AjaxHelpers, NotesVisibilityFactory, Helpers
) {
    'use strict';
    describe('EdxNotes ToggleNotesFactory', function() {
        var params = {
            endpoint: '/test_endpoint',
            user: 'a user',
            usageId: 'an usage',
            courseId: 'a course',
            token: Helpers.makeToken(),
            tokenUrl: '/test_token_url'
        };

        beforeEach(function() {
            loadFixtures(
                'js/fixtures/edxnotes/edxnotes_wrapper.html',
                'js/fixtures/edxnotes/toggle_notes.html'
            );
            NotesVisibilityFactory.VisibilityDecorator.factory(
                document.getElementById('edx-notes-wrapper-123'), params, true
            );
            NotesVisibilityFactory.VisibilityDecorator.factory(
                document.getElementById('edx-notes-wrapper-456'), params, true
            );
            this.toggleNotes = NotesVisibilityFactory.ToggleVisibilityView(true, '/test_url');
            this.button = $('.action-toggle-notes');
            this.label = this.button.find('.utility-control-label');
            this.toggleMessage = $('.action-toggle-message');
            spyOn(this.toggleNotes, 'toggleHandler').and.callThrough();
        });

        afterEach(function () {
            NotesVisibilityFactory.VisibilityDecorator._setVisibility(null);
            while (Annotator._instances.length > 0) {
                Annotator._instances[0].destroy();
            }
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

            // TODO: why is the same search request made twice?
            AjaxHelpers.expectJsonRequest(requests, 'GET',
                '/test_endpoint/search/?user=a+user&usage_id=an+usage&course_id=a+course'
            );
            AjaxHelpers.respondWithJson(requests, {});
            AjaxHelpers.expectJsonRequest(requests, 'GET',
                '/test_endpoint/search/?user=a+user&usage_id=an+usage&course_id=a+course'
            );
            AjaxHelpers.respondWithJson(requests, {});

            AjaxHelpers.expectJsonRequest(requests, 'PUT', '/test_url', {
                'visibility': true
            });
            AjaxHelpers.respondWithJson(requests, {});
        });

        it('can handle errors', function() {
            var requests = AjaxHelpers.requests(this),
                $errorContainer = $('.annotator-notice');

            this.button.click();
            AjaxHelpers.respondWithError(requests);
            expect($errorContainer).toContainText(
                'An error has occurred. Make sure that you are connected to the Internet, ' +
                'and then try refreshing the page.'
            );
            expect($errorContainer).toBeVisible();
            expect($errorContainer).toHaveClass('annotator-notice-show');
            expect($errorContainer).toHaveClass('annotator-notice-error');

            this.button.click();

            // TODO: why is the same search request made twice?
            AjaxHelpers.expectJsonRequest(requests, 'GET',
                '/test_endpoint/search/?user=a+user&usage_id=an+usage&course_id=a+course'
            );
            AjaxHelpers.respondWithJson(requests, {});
            AjaxHelpers.expectJsonRequest(requests, 'GET',
                '/test_endpoint/search/?user=a+user&usage_id=an+usage&course_id=a+course'
            );
            AjaxHelpers.respondWithJson(requests, {});

            AjaxHelpers.respondWithJson(requests, {});
            expect($errorContainer).not.toHaveClass('annotator-notice-show');
        });

        it('toggles notes when CTRL + SHIFT + [ keydown on document', function() {
            // Character '[' has keyCode 219
            $(document).trigger($.Event('keydown', {keyCode: 219, ctrlKey: true, shiftKey: true}));
            expect(this.toggleNotes.toggleHandler).toHaveBeenCalled();
        });
    });
});
