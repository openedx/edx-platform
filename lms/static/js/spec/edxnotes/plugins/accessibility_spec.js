define([
    'jquery', 'underscore', 'annotator_1.2.9', 'logger', 'js/edxnotes/views/notes_factory'
], function($, _, Annotator, Logger, NotesFactory) {
    'use strict';
    describe('EdxNotes Accessibility Plugin', function() {
        function keyDownEvent(key) {
            return $.Event('keydown', {keyCode: key});
        }

        function tabBackwardEvent() {
            return $.Event('keydown', {keyCode: $.ui.keyCode.TAB, shiftKey: true});
        }

        function tabForwardEvent() {
            return $.Event('keydown', {keyCode: $.ui.keyCode.TAB, shiftKey: false});
        }

        function enterMetaKeyEvent() {
            return $.Event('keydown', {keyCode: $.ui.keyCode.ENTER, metaKey: true});
        }

        function enterControlKeyEvent() {
            return $.Event('keydown', {keyCode: $.ui.keyCode.ENTER, ctrlKey: true});
        }

        beforeEach(function() {
            this.KEY = $.ui.keyCode;
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.annotator = NotesFactory.factory(
                $('div#edx-notes-wrapper-123').get(0), {
                    endpoint: 'http://example.com/'
                }
            );
            this.plugin = this.annotator.plugins.Accessibility;
            spyOn(Logger, 'log');
        });

        afterEach(function() {
            while (Annotator._instances.length > 0) {
                Annotator._instances[0].destroy();
            }
        });

        describe('destroy', function() {
            it('should unbind all events', function() {
                spyOn($.fn, 'off');
                spyOn(this.annotator, 'unsubscribe').and.callThrough();
                this.plugin.destroy();
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationViewerTextField', this.plugin.addAriaAttributes
                );
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationsLoaded', this.plugin.addDescriptions
                );
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationCreated', this.plugin.addDescriptions
                );
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationCreated', this.plugin.focusOnHighlightedText
                );
                expect(this.annotator.unsubscribe).toHaveBeenCalledWith(
                    'annotationDeleted', this.plugin.removeDescription
                );
                expect($.fn.off).toHaveBeenCalledWith('.accessibility');
            });
        });

        describe('a11y attributes', function() {
            var highlight, annotation, note;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: 'Test text',
                    highlights: [highlight.get(0)]
                };
            });

            it('should be added to highlighted text and associated note', function() {
                this.annotator.viewer.load([annotation]);
                note = $('.annotator-note');
                expect(note).toExist();
                expect(note).toHaveAttr('tabindex', '-1');
                expect(note).toHaveAttr('role', 'note');
                expect(note).toHaveAttr('class', 'annotator-note');
            });

            it('should create aria-descriptions when annotations are loaded', function() {
                this.annotator.publish('annotationsLoaded', [[annotation]]);
                expect(highlight).toHaveAttr('aria-describedby', 'aria-note-description-01');
                expect($('#aria-note-description-01')).toContainText('Test text');
            });

            it('should create aria-description when new annotation is created', function() {
                this.annotator.publish('annotationCreated', [annotation]);
                expect(highlight).toHaveAttr('aria-describedby', 'aria-note-description-01');
                expect($('#aria-note-description-01')).toContainText('Test text');
            });

            it('should remove aria-description when the annotation is removed', function() {
                this.annotator.publish('annotationDeleted', [annotation]);
                expect($('#aria-note-description-01')).not.toExist();
            });
        });

        describe('keydown events on highlighted text', function() {
            var highlight, annotation, note;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: 'Test text',
                    highlights: [highlight.get(0)]
                };
                highlight.data('annotation', annotation);
                spyOn(this.annotator, 'showViewer').and.callThrough();
                spyOn(this.annotator.viewer, 'hide').and.callThrough();
                spyOn(this.plugin, 'focusOnGrabber').and.callThrough();
            });

            it('should open the viewer on SPACE keydown and focus on note', function() {
                highlight.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.showViewer).toHaveBeenCalled();
            });

            it('should open the viewer on ENTER keydown and focus on note', function() {
                highlight.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.showViewer).toHaveBeenCalled();
            });

            // This happens only when coming from notes page
            it('should open focus on viewer on TAB keydown if viewer is opened', function() {
                this.annotator.viewer.load([annotation]);
                highlight.trigger(keyDownEvent(this.KEY.TAB));
                expect(this.annotator.element.find('.annotator-listing')).toBeFocused();
            });

            it('should focus highlighted text after closing', function() {
                var note;
                highlight.trigger(keyDownEvent(this.KEY.ENTER));
                note = this.annotator.element.find('.annotator-edit');
                note.trigger(keyDownEvent(this.KEY.ESCAPE));
                expect(highlight).toBeFocused();
            });

            it('should focus on grabber after being deleted', function() {
                highlight.trigger(keyDownEvent(this.KEY.ENTER));
                this.annotator.publish('annotationDeleted', {});
                expect(this.plugin.focusGrabber).toBeFocused();
            });

            it('should not focus on grabber when the viewer is hidden', function() {
                this.annotator.publish('annotationDeleted', {});
                expect(this.plugin.focusGrabber).not.toBeFocused();
            });
        });

        describe('keydown events on viewer', function() {
            var highlight, annotation, listing, note, edit, del, close;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: 'Test text',
                    highlights: [highlight.get(0)]
                };
                highlight.data('annotation', annotation);
                this.annotator.viewer.load([annotation]);
                listing = this.annotator.element.find('.annotator-listing').first();
                note = this.annotator.element.find('.annotator-note').first();
                edit = this.annotator.element.find('.annotator-edit').first();
                del = this.annotator.element.find('.annotator-delete').first();
                close = this.annotator.element.find('.annotator-close').first();
                spyOn(this.annotator.viewer, 'hide').and.callThrough();
            });

            it('should give focus to Note on Listing TAB keydown', function() {
                listing.focus();
                listing.trigger(tabForwardEvent());
                expect(note).toBeFocused();
            });

            it('should give focus to Close on Listing SHIFT + TAB keydown', function() {
                listing.focus();
                listing.trigger(tabBackwardEvent());
                expect(close).toBeFocused();
            });

            it('should cycle forward through Note, Edit, Delete, and Close on TAB keydown', function() {
                note.focus();
                note.trigger(tabForwardEvent());
                expect(edit).toBeFocused();
                edit.trigger(tabForwardEvent());
                expect(del).toBeFocused();
                del.trigger(tabForwardEvent());
                expect(close).toBeFocused();
                close.trigger(tabForwardEvent());
                expect(note).toBeFocused();
            });

            it('should cycle backward through Note, Edit, Delete, and Close on SHIFT + TAB keydown', function() {
                note.focus();
                note.trigger(tabBackwardEvent());
                expect(close).toBeFocused();
                close.trigger(tabBackwardEvent());
                expect(del).toBeFocused();
                del.trigger(tabBackwardEvent());
                expect(edit).toBeFocused();
                edit.trigger(tabBackwardEvent());
                expect(note).toBeFocused();
            });

            it('should hide on ESCAPE keydown', function() {
                var tabControls = [listing, note, edit, del, close];

                _.each(tabControls, function(control) {
                    control.focus();
                    control.trigger(keyDownEvent(this.KEY.ESCAPE));
                }, this);
                expect(this.annotator.viewer.hide.calls.count()).toBe(5);
            });
        });

        describe('keydown events on editor', function() {
            var highlight, annotation, form, annotatorItems, textArea, tags, save, cancel;

            beforeEach(function() {
                highlight = $('<span class="annotator-hl" tabindex="0"/>').appendTo(this.annotator.element);
                annotation = {
                    id: '01',
                    text: 'Test text',
                    highlights: [highlight.get(0)]
                };
                highlight.data('annotation', annotation);
                this.annotator.editor.show(annotation, {'left': 0, 'top': 0});
                form = this.annotator.element.find('form.annotator-widget');
                annotatorItems = this.annotator.element.find('.annotator-item');
                textArea = annotatorItems.first().children('textarea');
                tags = annotatorItems.first().next().children('input');
                save = this.annotator.element.find('.annotator-save');
                cancel = this.annotator.element.find('.annotator-cancel');
                spyOn(this.annotator.editor, 'submit').and.callThrough();
                spyOn(this.annotator.editor, 'hide').and.callThrough();
            });

            it('should give focus to TextArea on Form TAB keydown', function() {
                form.focus();
                form.trigger(tabForwardEvent());
                expect(textArea).toBeFocused();
            });

            it('should give focus to Cancel on Form SHIFT + TAB keydown', function() {
                form.focus();
                form.trigger(tabBackwardEvent());
                expect(cancel).toBeFocused();
            });

            it('should cycle forward through textarea, tags, save, and cancel on TAB keydown', function() {
                textArea.focus();
                textArea.trigger(tabForwardEvent());
                expect(tags).toBeFocused();
                tags.trigger(tabForwardEvent());
                expect(save).toBeFocused();
                save.trigger(tabForwardEvent());
                expect(cancel).toBeFocused();
                cancel.trigger(tabForwardEvent());
                expect(textArea).toBeFocused();
            });

            it('should cycle back through textarea, tags, save, and cancel on SHIFT + TAB keydown', function() {
                textArea.focus();
                textArea.trigger(tabBackwardEvent());
                expect(cancel).toBeFocused();
                cancel.trigger(tabBackwardEvent());
                expect(save).toBeFocused();
                save.trigger(tabBackwardEvent());
                expect(tags).toBeFocused();
                tags.trigger(tabBackwardEvent());
                expect(textArea).toBeFocused();
            });

            it('should submit if target is Save on ENTER or SPACE keydown', function() {
                save.focus();
                save.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.editor.submit).toHaveBeenCalled();
                this.annotator.editor.submit.calls.reset();
                save.focus();
                save.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.editor.submit).toHaveBeenCalled();
            });

            it('should submit on META or CONTROL + ENTER keydown', function() {
                textArea.focus();
                textArea.trigger(enterMetaKeyEvent());
                expect(this.annotator.editor.submit).toHaveBeenCalled();
                this.annotator.editor.submit.calls.reset();
                textArea.focus();
                textArea.trigger(enterControlKeyEvent());
                expect(this.annotator.editor.submit).toHaveBeenCalled();
            });

            it('should hide if target is Cancel on ENTER or SPACE keydown', function() {
                cancel.focus();
                cancel.trigger(keyDownEvent(this.KEY.ENTER));
                expect(this.annotator.editor.hide).toHaveBeenCalled();
                this.annotator.editor.hide.calls.reset();
                cancel.focus();
                save.trigger(keyDownEvent(this.KEY.SPACE));
                expect(this.annotator.editor.hide).toHaveBeenCalled();
            });

            it('should hide on ESCAPE keydown', function() {
                var tabControls = [textArea, save, cancel];

                _.each(tabControls, function(control) {
                    control.focus();
                    control.trigger(keyDownEvent(this.KEY.ESCAPE));
                }, this);
                expect(this.annotator.editor.hide.calls.count()).toBe(3);
            });
        });
    });
});
