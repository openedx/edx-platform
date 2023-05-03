define([
    'jquery', 'underscore', 'annotator_1.2.9', 'js/edxnotes/views/notes_factory',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'js/edxnotes/utils/notes_collector', 'js/spec/edxnotes/helpers'
], function($, _, Annotator, NotesFactory, AjaxHelpers, NotesCollector, Helpers) {
    'use strict';
    describe('EdxNotes NotesFactory', function() {
        beforeEach(function() {
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            NotesCollector.cleanup();
        });

        afterEach(function() {
            while (Annotator._instances.length > 0) {
                Annotator._instances[0].destroy();
            }
        });

        it('can initialize annotator correctly', function(done) {
            var requests = AjaxHelpers.requests(this),
                token = Helpers.makeToken(),
                options = {
                    user: 'a user',
                    usage_id: 'an usage',
                    course_id: 'a course'
                };

            _.each($('.edx-notes-wrapper'), function(wrapper) {
                var annotator = NotesFactory.factory(wrapper, {
                    endpoint: '/test_endpoint',
                    user: 'a user',
                    usageId: 'an usage',
                    courseId: 'a course',
                    token: token,
                    tokenUrl: '/test_token_url'
                });

                expect(annotator.options.auth.tokenUrl).toBe('/test_token_url');
                expect(annotator.options.store.prefix).toBe('/test_endpoint');
                expect(annotator.options.store.annotationData).toEqual(options);
                expect(annotator.options.store.loadFromSearch).toEqual(options);
            });
            jasmine.waitUntil(function() {
                return requests.length === 1;
            }).done(function() {
                expect(requests[0].requestHeaders['x-annotator-auth-token']).toBe(token);
                done();
            });
        });
    });
});
