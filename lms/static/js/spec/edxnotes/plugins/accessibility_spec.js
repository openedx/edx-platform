define([
    'jquery', 'underscore', 'annotator_1.2.9', 'logger', 'js/edxnotes/views/notes_factory', 'js/spec/edxnotes/custom_matchers'
], function($, _, Annotator, Logger, NotesFactory, customMatchers) {
    'use strict';
    describe('EdxNotes Accessibility Plugin', function() {
        function keyDownEvent (key) {
            return $.Event('keydown', {keyCode: key});
        }

        function tabBackwardEvent () {
            return $.Event('keydown', {keyCode: $.ui.keyCode.TAB, shiftKey: true});
        }

        function tabForwardEvent () {
            return $.Event('keydown', {keyCode: $.ui.keyCode.TAB, shiftKey: false});
        }

        function enterMetaKeyEvent () {
            return $.Event('keydown', {keyCode: $.ui.keyCode.ENTER, metaKey: true});
        }

        function enterControlKeyEvent () {
            return $.Event('keydown', {keyCode: $.ui.keyCode.ENTER, ctrlKey: true});
        }

        beforeEach(function() {
            this.KEY = $.ui.keyCode;
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.annotator =  NotesFactory.factory(
                $('div#edx-notes-wrapper-123').get(0), {
                    endpoint: 'http://example.com/'
                }
            );
            this.plugin = this.annotator.plugins.Accessibility;
            spyOn(Logger, 'log');
        });

        afterEach(function () {
            _.invoke(Annotator._instances, 'destroy');
        });

        describe('destroy', function () {
            it('should unbind all events', function () {
                spyOn($.fn, 'off');
                spyOn(this.annotator, 'unsubscribe');
                this.plugin.destroy();
                expect($.fn.off).toHaveBeenCalledWith('keydown', '.annotator-hl');
                expect($.fn.off).toHaveBeenCalledWith('keydown', '.annotator-viewer');
                expect($.fn.off).toHaveBeenCalledWith('keydown', '.annotator-editor');
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationViewerTextField', this.plugin.addAriaAttributes
                );
            });
        });

        describe('a11y attibutes', function () {
            var highlight, annotation, note;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: "Test text",
                    highlights: [highlight.get(0)]
                };
            });

            it('should be added to highlighted text and associated note', function () {
                this.annotator.viewer.load([annotation]);
                note = $('#aria-note-01');
                expect(highlight).toHaveAttr('aria-describedby', 'aria-note-01');
                expect(note).toExist();
                expect(note).toHaveAttr('tabindex', -1);
                expect(note).toHaveAttr('role', 'note');
                expect(note).toHaveAttr('aria-label', 'Note');
                expect(note).toHaveAttr('class', 'annotator-note');
            });
        });

        describe('keydown events on highlighted text', function () {
            var highlight, annotation, note;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: "Test text",
                    highlights: [highlight.get(0)]
                };
                spyOn(this.annotator, 'showViewer').andCallThrough();
                spyOn(this.annotator.viewer, 'hide').andCallThrough();
            });

            it('should open the viewer on SPACE keydown and focus on note', function () {
                highlight.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.showViewer).toHaveBeenCalled();
                // TODO: Check that note is focused
                // note = this.annotator.element.find('.annotator-note').first();
                // expect(note).toBeFocused();
            });

            it('should open the viewer on ENTER keydown and focus on note', function () {
                highlight.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.showViewer).toHaveBeenCalled();
                // TODO: Check that note is focused
                // note = this.annotator.element.find('.annotator-note').first();
                // expect(note).toBeFocused();
            });
        });

        describe('keydown events on viewer', function () {
            var html, outerHighlight, innerHighlight, annotations, notes = [], edits = [], dels = [], closes = [];

            beforeEach(function() {
                html = [
                    '<span class="annotator-hl" tabindex="0">',
                        'Outer highlight containing an ',
                        '<span class="annotator-hl" tabindex="0">',
                            'inner highlight',
                        '</span>',
                        'in its text.',
                    '</span>'
                ].join('');
                outerHighlight = $(html).appendTo(this.annotator.element);
                innerHighlight = outerHighlight.children();
                annotations = [
                    {
                        id: '01',
                        text: 'Outer highlight note',
                        highlights: [outerHighlight.get(0)]
                    },
                    {
                        id: '02',
                        text: 'Inner highlight note',
                        highlights: [innerHighlight.get(0)]
                    }
                ];
                this.annotator.viewer.load(annotations);
                notes[0] = this.annotator.element.find('.annotator-note').first();
                edits[0] = this.annotator.element.find('.annotator-edit').first();
                dels[0] = this.annotator.element.find('.annotator-delete').first();
                closes[0] = this.annotator.element.find('.annotator-close').first();
                notes[1] = this.annotator.element.find('.annotator-note').last();
                edits[1] = this.annotator.element.find('.annotator-edit').last();
                dels[1] = this.annotator.element.find('.annotator-delete').last();
                closes[1] = this.annotator.element.find('.annotator-close').last();
                spyOn(this.annotator.viewer, 'hide').andCallThrough();;
            });

            it('should cycle forward through the multiple Note, Edit, Delete, and Close on TAB keydown', function () {
                // TODO: Improve this code
                notes[0].focus();
                notes[0].trigger(tabForwardEvent());
                expect(edits[0]).toBeFocused();
                edits[0].trigger(tabForwardEvent());
                expect(dels[0]).toBeFocused();
                dels[0].trigger(tabForwardEvent());
                expect(closes[0]).toBeFocused();
                closes[0].trigger(tabForwardEvent());
                expect(notes[1]).toBeFocused();
                notes[1].trigger(tabForwardEvent());
                expect(edits[1]).toBeFocused();
                edits[1].trigger(tabForwardEvent());
                expect(dels[1]).toBeFocused();
                dels[1].trigger(tabForwardEvent());
                expect(closes[1]).toBeFocused();
                closes[1].trigger(tabForwardEvent());
                expect(notes[0]).toBeFocused();
            });

            it('should cycle backward through the multiple Note, Edit, Delete, and Close on SHIFT + TAB keydown', function () {
                // TODO: Improve this code
                notes[0].focus();
                notes[0].trigger(tabBackwardEvent());
                expect(closes[1]).toBeFocused();
                closes[1].trigger(tabBackwardEvent());
                expect(dels[1]).toBeFocused();
                dels[1].trigger(tabBackwardEvent());
                expect(edits[1]).toBeFocused();
                edits[1].trigger(tabBackwardEvent());
                expect(notes[1]).toBeFocused();
                notes[1].trigger(tabBackwardEvent());
                expect(closes[0]).toBeFocused();
                closes[0].trigger(tabBackwardEvent());
                expect(dels[0]).toBeFocused();
                dels[0].trigger(tabBackwardEvent());
                expect(edits[0]).toBeFocused();
                edits[0].trigger(tabBackwardEvent());
                expect(notes[0]).toBeFocused();
            });

            it('should close the viewer and give focus back to highlight on ESCAPE keydown', function () {
                edits[0].focus();
                edits[0].trigger(keyDownEvent(this.KEY.ESCAPE));
                expect(this.annotator.viewer.hide).toHaveBeenCalled();
                expect(outerHighlight).toBeFocused();
                dels[0].focus();
                dels[0].trigger(keyDownEvent(this.KEY.ESCAPE));
                expect(this.annotator.viewer.hide).toHaveBeenCalled();
                expect(outerHighlight).toBeFocused();
            });
        });

        describe('keydown events on editor', function () {
            var highlight, annotation, textArea, save, cancel;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: "Test text",
                    highlights: [highlight.get(0)]
                };
                this.annotator.editor.show(annotation, {'left': 0, 'top': 0});
                textArea = this.annotator.element.find('.annotator-item').first().children('textarea');
                save  = this.annotator.element.find('.annotator-save');
                cancel = this.annotator.element.find('.annotator-cancel');
                spyOn(this.annotator.editor, 'submit').andCallThrough();
                spyOn(this.annotator.editor, 'hide').andCallThrough();
            });

            it('should cycle forward through texarea, save, and cancel on TAB keydown', function () {
                expect(textArea).toBeFocused();
                textArea.trigger(tabForwardEvent());
                expect(save).toBeFocused();
                save.trigger(tabForwardEvent());
                expect(cancel).toBeFocused();
                cancel.trigger(tabForwardEvent());
                expect(textArea).toBeFocused();
            });

            it('should cycle back through texarea, save, and cancel on SHIFT + TAB keydown', function () {
                expect(textArea).toBeFocused();
                textArea.trigger(tabBackwardEvent());
                expect(cancel).toBeFocused();
                cancel.trigger(tabBackwardEvent());
                expect(save).toBeFocused();
                save.trigger(tabBackwardEvent());
                expect(textArea).toBeFocused();
            });

            it('should submit if target is Save on ENTER or SPACE keydown', function () {
                save.focus();
                save.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.editor.submit).toHaveBeenCalled();
                this.annotator.editor.submit.reset();
                save.focus();
                save.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.editor.submit).toHaveBeenCalled();
            });

            it('should submit on META or CONTROL + ENTER keydown', function () {
                textArea.focus();
                textArea.trigger(enterMetaKeyEvent());
                expect(this.annotator.editor.submit).toHaveBeenCalled();
                this.annotator.editor.submit.reset();
                textArea.focus();
                textArea.trigger(enterControlKeyEvent());
                expect(this.annotator.editor.submit).toHaveBeenCalled();
            });

            it('should hide if target is Cancel on ENTER or SPACE keydown', function () {
                cancel.focus();
                cancel.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.editor.hide).toHaveBeenCalled();
                this.annotator.editor.hide.reset();
                cancel.focus();
                save.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.editor.hide).toHaveBeenCalled();
            });

            it('should hide on ESCAPE keydown', function () {
                textArea.focus();
                textArea.trigger(keyDownEvent(this.KEY.ESCAPE));
                expect(this.annotator.editor.hide).toHaveBeenCalled();
            });
        });
    });
});
