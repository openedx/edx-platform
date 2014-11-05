define(['jquery', 'underscore', 'js/edxnotes/notes', 'jasmine-jquery'],
    function($, _, Notes) {
        'use strict';

        describe('Test Shim', function() {
            var annotators = [], highlights = [];

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

            function checkClickEventsNotBound(namespace) {
                var events = $._data(document, 'events').click;

                _.each(events, function(event) {
                    expect(event.namespace.indexOf(namespace)).toBeGreaterThan(-1);
                });
            }

            beforeEach(function() {
                loadFixtures('js/fixtures/edxnotes/edxnotes.html');
                highlights = [];
                annotators = [
                    Notes.factory($('div#edx-notes-wrapper-123').get(0), {}),
                    Notes.factory($('div#edx-notes-wrapper-456').get(0), {})
                ];
                _.each(annotators, function(annotator, index) {
                    highlights.push($('<span class="annotator-hl" />').appendTo(annotators[index].element));
                    spyOn(annotator, 'onHighlightClick').andCallThrough();
                    spyOn(annotator, 'onHighlightMouseover').andCallThrough();
                    spyOn(annotator, 'startViewerHideTimer').andCallThrough();
                });
            });

            it('Test that clicking a highlight freezes mouseover and mouseout in all highlighted text', function() {
                _.each(annotators, function(annotator) {
                    expect(annotator.isFrozen).toBe(false);
                });
                highlights[0].click();
                // Click is attached to the onHighlightClick event handler which
                // in turn calls onHighlightMouseover.
                // To test if onHighlightMouseover is called or not on
                // mouseover, we'll have to reset onHighlightMouseover.
                expect(annotators[0].onHighlightClick).toHaveBeenCalled();
                expect(annotators[0].onHighlightMouseover).toHaveBeenCalled();
                annotators[0].onHighlightMouseover.reset();

                // Check that both instances of annotator are frozen
                _.invoke(highlights, 'mouseover');
                _.invoke(highlights, 'mouseout');
                _.each(annotators, function(annotator) {
                    checkAnnotatorIsFrozen(annotator);
                });
            });

            it('Test that clicking twice reverts to default behavior', function() {
                highlights[0].click();
                $(document).click();
                annotators[0].onHighlightMouseover.reset();

                // Check that both instances of annotator are unfrozen
                _.invoke(highlights, 'mouseover');
                _.invoke(highlights, 'mouseout');
                _.each(annotators, function(annotator) {
                    checkAnnotatorIsUnfrozen(annotator);
                });
            });

            it('Test that destroying an instance with an open viewer sets all other instances' +
               'to unfrozen and unbinds document click.edxnotes:freeze event handlers', function() {
                // Freeze all instances
                highlights[0].click();
                // Destroy first instance
                annotators[0].destroy();

                // Check that all click.edxnotes:freeze are unbound
                checkClickEventsNotBound('edxnotes:freeze');

                // Check that the remaining instance is unfrozen
                highlights[1].mouseover();
                highlights[1].mouseout();
                checkAnnotatorIsUnfrozen(annotators[1]);
            });

            it('Test that destroying an instance with an closed viewer only unfreezes that instance' +
               'and unbinds one document click.edxnotes:freeze event handlers', function() {
                // Freeze all instances
                highlights[0].click();
                annotators[0].onHighlightMouseover.reset();
                // Destroy second instance
                annotators[1].destroy();

                // Check that the first instance is frozen
                highlights[0].mouseover();
                highlights[0].mouseout();
                checkAnnotatorIsFrozen(annotators[0]);

                // Check that second one doesn't have a bound click.edxnotes:freeze
                checkClickEventsNotBound('edxnotes:freeze'+annotators[1].uid);
            });
        });
    }
);
