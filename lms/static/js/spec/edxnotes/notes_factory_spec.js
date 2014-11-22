define([
    'jquery', 'js/edxnotes/views/notes_factory', 'js/common_helpers/ajax_helpers',
    'jasmine-jquery'
],
function($, Notes, AjaxHelpers) {
    'use strict';
    describe('EdxNotes Notes', function() {
        var wrapper;

        beforeEach(function() {
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            wrapper = $('div#edx-notes-wrapper-123');
        });

        it('Tests that annotator is initialized with options correctly', function() {
            var requests = AjaxHelpers.requests(this),
                internalOptions = {
                    user: 'a user',
                    usage_id : 'an usage',
                    course_id: 'a course'
                },
                annotator = Notes.factory(wrapper[0], {
                    endpoint: 'test_endpoint',
                    user: 'a user',
                    usageId : 'an usage',
                    courseId: 'a course',
                    token: 'test_token'
                }),
                request = requests[0];

            expect(requests.length).toBe(1);
            expect(request.requestHeaders['x-annotator-auth-token']).toBe('test_token');
            expect(annotator.options.store.prefix).toBe('test_endpoint');
            expect(annotator.options.store.annotationData).toEqual(internalOptions);
            expect(annotator.options.store.loadFromSearch).toEqual(internalOptions);
        });
    });
});
