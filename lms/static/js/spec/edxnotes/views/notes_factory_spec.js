define([
    'annotator_1.2.9', 'js/edxnotes/views/notes_factory', 'common/js/spec_helpers/ajax_helpers',
    'js/spec/edxnotes/helpers', 'js/spec/edxnotes/custom_matchers'
], function(Annotator, NotesFactory, AjaxHelpers, Helpers, customMatchers) {
    'use strict';
    describe('EdxNotes NotesFactory', function() {
        beforeEach(function() {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.wrapper = document.getElementById('edx-notes-wrapper-123');
        });

        afterEach(function () {
            _.invoke(Annotator._instances, 'destroy');
        });

        it('can initialize annotator correctly', function() {
            var requests = AjaxHelpers.requests(this),
                token = Helpers.makeToken(),
                options = {
                    user: 'a user',
                    usage_id : 'an usage',
                    course_id: 'a course'
                },
                annotator = NotesFactory.factory(this.wrapper, {
                    endpoint: '/test_endpoint',
                    user: 'a user',
                    usageId : 'an usage',
                    courseId: 'a course',
                    token: token,
                    tokenUrl: '/test_token_url'
                }),
                request = requests[0];

            expect(requests).toHaveLength(1);
            expect(request.requestHeaders['x-annotator-auth-token']).toBe(token);
            expect(annotator.options.auth.tokenUrl).toBe('/test_token_url');
            expect(annotator.options.store.prefix).toBe('/test_endpoint');
            expect(annotator.options.store.annotationData).toEqual(options);
            expect(annotator.options.store.loadFromSearch).toEqual(options);
        });
    });
});
