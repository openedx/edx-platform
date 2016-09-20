define([
    'jquery', 'underscore', 'annotator_1.2.9', 'logger', 'js/edxnotes/views/notes_factory'
], function($, _, Annotator, Logger, NotesFactory) {
    'use strict';
    describe('EdxNotes CaretNavigation Plugin', function() {

        beforeEach(function() {
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.annotator =  NotesFactory.factory(
                $('div#edx-notes-wrapper-123').get(0), {
                    endpoint: 'http://example.com/'
                }
            );
            this.plugin = this.annotator.plugins.CaretNavigation;
            spyOn(Logger, 'log');
        });

        afterEach(function () {
            while (Annotator._instances.length > 0) {
                Annotator._instances[0].destroy();
            }
        });

        describe('destroy', function () {
            it('should unbind all events', function () {
                spyOn($.fn, 'off');
                this.plugin.destroy();
                expect($.fn.off).toHaveBeenCalledWith('keyup', this.plugin.onKeyUp);
            });
        });

        describe('isShortcut', function () {
            it('should return `true` if it is a shortcut', function () {
                expect(this.plugin.isShortcut($.Event('keyup', {
                    ctrlKey: true,
                    shiftKey: true,
                    keyCode: 221
                }))).toBeTruthy();
            });

            it('should return `false` if it is not a shortcut', function () {
                expect(this.plugin.isShortcut($.Event('keyup', {
                    ctrlKey: false,
                    shiftKey: true,
                    keyCode: 221
                }))).toBeFalsy();

                expect(this.plugin.isShortcut($.Event('keyup', {
                    ctrlKey: true,
                    shiftKey: true,
                    keyCode: $.ui.keyCode.TAB
                }))).toBeFalsy();
            });
        });

        describe('hasSelection', function () {
            it('should return `true` if has selection', function () {
                expect(this.plugin.hasSelection([{}, {}])).toBeTruthy();
            });

            it('should return `false` if does not have selection', function () {
                expect(this.plugin.hasSelection([])).toBeFalsy();
                expect(this.plugin.hasSelection()).toBeFalsy();
            });
        });

        describe('onKeyUp', function () {
            var triggerEvent = function (element, props) {
                var eventProps = $.extend({
                    ctrlKey: true,
                    shiftKey: true,
                    keyCode: 221
                }, props);
                element.trigger($.Event('keyup', eventProps));
            };

            beforeEach(function() {
                this.element = $('<span />', {'class': 'annotator-hl'}).appendTo(this.annotator.element);

                this.annotation = {
                    text: "test",
                    highlights: [this.element.get(0)]
                };

                this.mockOffset = {top: 0, left:0};

                this.mockSubscriber = jasmine.createSpy();
                this.annotator.subscribe('annotationCreated', this.mockSubscriber);

                spyOn($.fn, 'position').and.returnValue(this.mockOffset);
                spyOn(this.annotator, 'createAnnotation').and.returnValue(this.annotation);
                spyOn(this.annotator, 'setupAnnotation').and.returnValue(this.annotation);
                spyOn(this.annotator, 'getSelectedRanges').and.returnValue([{}]);
                spyOn(this.annotator, 'deleteAnnotation');
                spyOn(this.annotator, 'showEditor');
                spyOn(Annotator.Util, 'readRangeViaSelection');
                spyOn(this.plugin, 'saveSelection');
                spyOn(this.plugin, 'restoreSelection');
            });

            it('should create a new annotation', function () {
                triggerEvent(this.element);
                expect(this.annotator.createAnnotation.calls.count()).toBe(1);
            });

            it('should set up the annotation', function () {
                triggerEvent(this.element);
                expect(this.annotator.setupAnnotation).toHaveBeenCalledWith(
                    this.annotation
                );
            });

            it('should display the Annotation#editor correctly if the Annotation#adder is hidden', function () {
                spyOn($.fn, 'is').and.returnValue(false);
                triggerEvent(this.element);
                expect($('annotator-hl-temporary').position.calls.count()).toBe(1);
                expect(this.annotator.showEditor).toHaveBeenCalledWith(
                    this.annotation, this.mockOffset
                );
            });

            it('should display the Annotation#editor in the same place as the Annotation#adder', function () {
                spyOn($.fn, 'is').and.returnValue(true);
                triggerEvent(this.element);
                expect(this.annotator.adder.position.calls.count()).toBe(1);
                expect(this.annotator.showEditor).toHaveBeenCalledWith(
                    this.annotation, this.mockOffset
                );
            });

            it('should hide the Annotation#adder', function () {
                spyOn($.fn, 'is').and.returnValue(true);
                spyOn($.fn, 'hide');
                triggerEvent(this.element);
                expect(this.annotator.adder.hide).toHaveBeenCalled();
            });

            it('should add temporary highlights to the document to show the user what they selected', function () {
                triggerEvent(this.element);
                expect(this.element).toHaveClass('annotator-hl');
                expect(this.element).toHaveClass('annotator-hl-temporary');
            });

            it('should persist the temporary highlights if the annotation is saved', function () {
                triggerEvent(this.element);
                this.annotator.publish('annotationEditorSubmit');
                expect(this.element).toHaveClass('annotator-hl');
                expect(this.element).not.toHaveClass('annotator-hl-temporary');
            });

            it('should trigger the `annotationCreated` event if the edit\'s saved', function () {
                triggerEvent(this.element);
                this.annotator.onEditorSubmit(this.annotation);
                expect(this.mockSubscriber).toHaveBeenCalledWith(this.annotation);
            });

            it('should call Annotator#deleteAnnotation if editing is cancelled', function () {
                triggerEvent(this.element);
                this.annotator.onEditorHide();
                expect(this.mockSubscriber).not.toHaveBeenCalledWith('annotationCreated');
                expect(this.annotator.deleteAnnotation).toHaveBeenCalledWith(
                    this.annotation
                );
            });

            it('should restore selection if editing is cancelled', function () {
                triggerEvent(this.element);
                this.plugin.savedRange = 'range';
                expect(this.plugin.saveSelection).toHaveBeenCalled();
                this.annotator.onEditorHide();
                expect(this.plugin.restoreSelection).toHaveBeenCalled();
            });

            it('should do nothing if the edit\'s saved', function () {
                triggerEvent(this.element);
                expect(this.plugin.saveSelection).toHaveBeenCalled();
                this.plugin.savedRange = 'range';
                this.annotator.onEditorSubmit();
                expect(Annotator.Util.readRangeViaSelection).not.toHaveBeenCalled();
                expect(this.plugin.savedRange).toBeNull();
                expect(this.plugin.restoreSelection).not.toHaveBeenCalled();
            });

            it('should do nothing if it is not a shortcut', function () {
                triggerEvent(this.element, {ctrlKey: false});
                expect(this.annotator.showEditor).not.toHaveBeenCalled();
            });

            it('should do nothing if empty selection', function () {
                this.annotator.getSelectedRanges.and.returnValue([]);
                triggerEvent(this.element);
                expect(this.annotator.showEditor).not.toHaveBeenCalled();
            });

            it('should do nothing if selection is in Annotator', function () {
                spyOn(this.annotator, 'isAnnotator').and.returnValue(true);
                triggerEvent(this.element);
                expect(this.annotator.showEditor).not.toHaveBeenCalled();
            });
        });
    });
});
