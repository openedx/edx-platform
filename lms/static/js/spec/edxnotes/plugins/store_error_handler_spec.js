define([
    'jquery', 'underscore', 'annotator_1.2.9',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'js/spec/edxnotes/helpers',
    'js/edxnotes/views/notes_factory'
], function($, _, Annotator, AjaxHelpers, Helpers, NotesFactory) {
    'use strict';
    describe('Store Error Handler Custom Message', function() {
        beforeEach(function() {
            spyOn(Annotator, 'showNotification');
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.wrapper = document.getElementById('edx-notes-wrapper-123');
        });

        afterEach(function() {
            _.invoke(Annotator._instances, 'destroy');
        });

        it('can handle custom error if sent from server', function() {
            var requests = AjaxHelpers.requests(this);
            var token = Helpers.makeToken();
            NotesFactory.factory(this.wrapper, {
                endpoint: '/test_endpoint',
                user: 'a user',
                usageId: 'an usage',
                courseId: 'a course',
                token: token,
                tokenUrl: '/test_token_url'
            });

            var errorMsg = 'can\'t create more notes';
            AjaxHelpers.respondWithError(requests, 400, {error_msg: errorMsg});
            expect(Annotator.showNotification).toHaveBeenCalledWith(errorMsg, Annotator.Notification.ERROR);
        });
    });
});
