define([
    'jquery', 'underscore', 'annotator_1.2.9', 'js/edxnotes/views/notes_factory',
    'js/spec/edxnotes/custom_matchers'
], function($, _, Annotator, NotesFactory, customMatchers) {
    'use strict';
    describe('EdxNotes Scroll Plugin', function() {
        var annotators, highlights;

        function checkAnnotatorIsFrozen(annotator) {
            expect(annotator.isFrozen).toBe(true);
            expect(annotator.onHighlightMouseover).not.toHaveBeenCalled();
            expect(annotator.startViewerHideTimer).not.toHaveBeenCalled();
        }

        function checkAnnotatorIsUnfrozen(annotator) {
            expect(annotator.isFrozen).toBe(false);
            expect(annotator.onHighlightMouseover).toHaveBeenCalled();
            expect(annotator.startViewerHideTimer).toHaveBeenCalled();
        }

        beforeEach(function() {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            annotators = [
                NotesFactory.factory($('div#edx-notes-wrapper-123').get(0), {
                    endpoint: 'http://example.com/'
                }),
                NotesFactory.factory($('div#edx-notes-wrapper-456').get(0), {
                    endpoint: 'http://example.com/'
                })
            ];

            highlights = _.map(annotators, function(annotator) {
                spyOn(annotator, 'onHighlightClick').andCallThrough();
                spyOn(annotator, 'onHighlightMouseover').andCallThrough();
                spyOn(annotator, 'startViewerHideTimer').andCallThrough();
                return $('<span></span>', {
                    'class': 'annotator-hl',
                    'tabindex': -1,
                    'text': 'some content'
                }).appendTo(annotator.element);
            });

            spyOn(annotators[0].plugins.Scroller, 'getIdFromLocationHash').andReturn('abc123');
            spyOn($.fn, 'unbind').andCallThrough();
        });

        afterEach(function () {
            _.invoke(Annotator._instances, 'destroy');
        });

        it('should scroll to a note, open it and freeze the annotator if its id is part of the url hash', function() {
            annotators[0].plugins.Scroller.onNotesLoaded([{
                id: 'abc123',
                highlights: [highlights[0]]
            }]);
            annotators[0].onHighlightMouseover.reset();
            expect(highlights[0]).toBeFocused();
            highlights[0].mouseover();
            highlights[0].mouseout();
            checkAnnotatorIsFrozen(annotators[0]);
        });

        it('should not do anything if the url hash contains a wrong id', function() {
            annotators[0].plugins.Scroller.onNotesLoaded([{
                id: 'def456',
                highlights: [highlights[0]]
            }]);
            expect(highlights[0]).not.toBeFocused();
            highlights[0].mouseover();
            highlights[0].mouseout();
            checkAnnotatorIsUnfrozen(annotators[0]);
        });

        it('should not do anything if the url hash contains an empty id', function() {
            annotators[0].plugins.Scroller.onNotesLoaded([{
                id: '',
                highlights: [highlights[0]]
            }]);
            expect(highlights[0]).not.toBeFocused();
            highlights[0].mouseover();
            highlights[0].mouseout();
            checkAnnotatorIsUnfrozen(annotators[0]);
        });

        it('should unbind onNotesLoaded on destruction', function() {
            annotators[0].plugins.Scroller.destroy();
            expect($.fn.unbind).toHaveBeenCalledWith(
                'annotationsLoaded',
                annotators[0].plugins.Scroller.onNotesLoaded
            );
        });
    });
});
