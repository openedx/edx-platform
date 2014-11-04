define(['jquery', 'annotator', 'js/edxnotes/notes', 'jasmine-jquery'],
    function($, Annotator, Notes) {
        'use strict';

        describe('Test notes', function() {
            var wrapper;

            beforeEach(function() {
                loadFixtures('js/fixtures/edxnotes/edxnotes.html');
                wrapper = $('div#edx-notes-wrapper-123');
            });

            it('Tests if fixture has been loaded', function() {
                expect(wrapper).toExist();
                expect(wrapper).toHaveClass('edx-notes-wrapper');
            });

            it('Tests if Annotator and Notes are defined', function() {
                expect(Annotator).toBeDefined();
                expect(Notes).toBeDefined();
            });
        });
    }
);
