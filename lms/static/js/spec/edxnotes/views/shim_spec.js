define([
    'jquery', 'underscore', 'annotator_1.2.9', 'js/edxnotes/views/notes_factory'
], function($, _, Annotator, NotesFactory) {
    'use strict';
    describe('EdxNotes Shim', function() {
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

        function checkClickEventsNotBound(namespace) {
            var events = $._data(document, 'events').click;

            _.each(events, function(event) {
                expect(event.namespace.indexOf(namespace)).toBe(-1);
            });
        }

        beforeEach(function() {
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            highlights = [];
            annotators = [
                NotesFactory.factory($('#edx-notes-wrapper-123').get(0), {
                    endpoint: 'http://example.com/'
                }),
                NotesFactory.factory($('#edx-notes-wrapper-456').get(0), {
                    endpoint: 'http://example.com/'
                })
            ];
            _.each(annotators, function(annotator) {
                highlights.push($('<span class="annotator-hl" />').appendTo(annotator.element));
                spyOn(annotator, 'onHighlightClick').and.callThrough();
                spyOn(annotator, 'onHighlightMouseover').and.callThrough();
                spyOn(annotator, 'startViewerHideTimer').and.callThrough();
            });
            spyOn($.fn, 'off').and.callThrough();
        });

        afterEach(function () {
            while (Annotator._instances.length > 0) {
                Annotator._instances[0].destroy();
            }
        });

        it('does not show the viewer if the editor is opened', function() {
            annotators[0].showEditor({}, {});
            highlights[0].mouseover();
            expect($('#edx-notes-wrapper-123 .annotator-editor')).not.toHaveClass('annotator-hide');
            expect($('#edx-notes-wrapper-123 .annotator-viewer')).toHaveClass('annotator-hide');
        });

        it('clicking on highlights does not open the viewer when the editor is opened', function() {
            spyOn(annotators[1].editor, 'isShown').and.returnValue(false);
            highlights[0].click();
            annotators[1].editor.isShown.and.returnValue(true);
            highlights[1].click();
            expect($('#edx-notes-wrapper-123 .annotator-viewer')).not.toHaveClass('annotator-hide');
            expect($('#edx-notes-wrapper-456 .annotator-viewer')).toHaveClass('annotator-hide');
        });

        it('clicking a highlight freezes mouseover and mouseout in all highlighted text', function() {
            _.each(annotators, function(annotator) {
                expect(annotator.isFrozen).toBe(false);
            });
            highlights[0].click();
            // Click is attached to the onHighlightClick event handler which
            // in turn calls onHighlightMouseover.
            // To test if onHighlightMouseover is called or not on
            // mouseover, we'll have to reset onHighlightMouseover.
            annotators[0].onHighlightMouseover.calls.reset();
            // Check that both instances of annotator are frozen
            _.invoke(highlights, 'mouseover');
            _.invoke(highlights, 'mouseout');
            _.each(annotators, checkAnnotatorIsFrozen);
        });

        it('clicking twice reverts to default behavior', function() {
            highlights[0].click();
            $(document).click();
            annotators[0].onHighlightMouseover.calls.reset();

            // Check that both instances of annotator are unfrozen
            _.invoke(highlights, 'mouseover');
            _.invoke(highlights, 'mouseout');
            _.each(annotators, function(annotator) {
                checkAnnotatorIsUnfrozen(annotator);
            });
        });

        it('destroying an instance with an open viewer sets all other instances' +
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

        it('destroying an instance with an closed viewer only unfreezes that instance' +
           'and unbinds one document click.edxnotes:freeze event handlers', function() {
            // Freeze all instances
            highlights[0].click();
            annotators[0].onHighlightMouseover.calls.reset();
            // Destroy second instance
            annotators[1].destroy();

            // Check that the first instance is frozen
            highlights[0].mouseover();
            highlights[0].mouseout();
            checkAnnotatorIsFrozen(annotators[0]);

            // Check that second one doesn't have a bound click.edxnotes:freeze
            checkClickEventsNotBound('edxnotes:freeze' + annotators[1].uid);
        });

        it('should unbind events on destruction', function() {
            annotators[0].destroy();
            expect($.fn.off).toHaveBeenCalledWith(
                'click', annotators[0].onNoteClick
            );
            expect($.fn.off).toHaveBeenCalledWith(
                'click', '.annotator-hl'
            );
        });

        it('should hide viewer when close button is clicked', function() {
            var close,
                annotation = {
                    id: '01',
                    text: "Test text",
                    highlights: [highlights[0].get(0)]
                };

            annotators[0].viewer.load([annotation]);
            close = annotators[0].viewer.element.find('.annotator-close');
            close.click();
            expect($('#edx-notes-wrapper-123 .annotator-viewer')).toHaveClass('annotator-hide');
        });

        describe('_setupViewer', function () {
            var mockViewer = null;

            beforeEach(function () {
                var  element = $('<div />');
                mockViewer = {
                    fields: [],
                    element: element
                };

                mockViewer.on = jasmine.createSpy().and.returnValue(mockViewer);
                mockViewer.hide = jasmine.createSpy().and.returnValue(mockViewer);
                mockViewer.destroy = jasmine.createSpy().and.returnValue(mockViewer);
                mockViewer.addField = jasmine.createSpy().and.callFake(function (options) {
                    mockViewer.fields.push(options);
                    return mockViewer;
                });

                spyOn(element, 'bind').and.returnValue(element);
                spyOn(element, 'appendTo').and.returnValue(element);
                spyOn(Annotator, 'Viewer').and.returnValue(mockViewer);

                annotators[0]._setupViewer();
            });

            it('should create a new instance of Annotator.Viewer and set Annotator#viewer', function () {
                expect(annotators[0].viewer).toEqual(mockViewer);
            });

            it('should hide the annotator on creation', function () {
                expect(mockViewer.hide.calls.count()).toBe(1);
            });

            it('should setup the default text field', function () {
                var args = mockViewer.addField.calls.mostRecent().args[0];

                expect(mockViewer.addField.calls.count()).toBe(1);
                expect(_.isFunction(args.load)).toBeTruthy();
            });

            it('should set the contents of the field on load', function () {
                var field = document.createElement('div'),
                    annotation = {text: 'text \nwith\r\nline\n\rbreaks \r'};

                annotators[0].viewer.fields[0].load(field, annotation);
                expect($(field).html()).toBe('text <br>with<br>line<br>breaks <br>');
            });

            it('should set the contents of the field to placeholder text when empty', function () {
                var field = document.createElement('div'),
                    annotation = {text: ''};

                annotators[0].viewer.fields[0].load(field, annotation);
                expect($(field).html()).toBe('<i>No Comment</i>');
            });

            it('should setup the default text field to publish an event on load', function () {
                var field = document.createElement('div'),
                    annotation = {text: ''},
                    callback = jasmine.createSpy();

                annotators[0].on('annotationViewerTextField', callback);
                annotators[0].viewer.fields[0].load(field, annotation);
                expect(callback).toHaveBeenCalledWith(field, annotation);
            });

            it('should subscribe to custom events', function () {
                expect(mockViewer.on).toHaveBeenCalledWith('edit', annotators[0].onEditAnnotation);
                expect(mockViewer.on).toHaveBeenCalledWith('delete', annotators[0].onDeleteAnnotation);
            });

            it('should bind to browser mouseover and mouseout events', function () {
                expect(mockViewer.element.bind).toHaveBeenCalledWith({
                    'mouseover': annotators[0].clearViewerHideTimer,
                    'mouseout':  annotators[0].startViewerHideTimer
                });
            });

            it('should append the Viewer#element to the Annotator#wrapper', function () {
                expect(mockViewer.element.appendTo).toHaveBeenCalledWith(annotators[0].wrapper);
            });
        });

        describe('TagsPlugin', function () {
            it('should add ARIA label information to the viewer', function() {
                var tagDiv,
                    annotation = {
                        id: '01',
                        text: "Test text",
                        tags: ["tag1", "tag2", "tag3"],
                        highlights: [highlights[0].get(0)]
                    };

                annotators[0].viewer.load([annotation]);
                tagDiv = annotators[0].viewer.element.find('.annotator-tags');
                expect($(tagDiv).attr('role')).toEqual('region');
                expect($(tagDiv).attr('aria-label')).toEqual('tags');

                // Three children for the individual tags.
                expect($(tagDiv).children().length).toEqual(3);
            });

            it('should add screen reader label to the editor', function() {
                var srLabel, editor, inputId;

                // We don't know exactly what the input ID will be (depends on number of annotatable components shown),
                // but the sr label "for" attribute should match the ID of the element immediately following it.
                annotators[0].showEditor({}, {});
                editor = annotators[0].editor;
                srLabel = editor.element.find("label.sr");
                inputId = srLabel.next().attr('id');
                expect(srLabel.attr('for')).toEqual(inputId);
            });
        });
    });
});
