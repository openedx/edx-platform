;(function (define, undefined) {
'use strict';
define(['jquery', 'underscore', 'annotator_1.2.9'], function ($, _, Annotator) {
    /**
     * The CaretNavigation Plugin which allows notes creation when users use
     * caret navigation to select the text.
     * Use `Ctrl + SPACE` or `Ctrl + ENTER` to open the editor.
     **/
    Annotator.Plugin.CaretNavigation = function () {
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
        _.bindAll(this, 'onKeyUp');
        Annotator.Plugin.apply(this, arguments);
    };

    $.extend(Annotator.Plugin.CaretNavigation.prototype, new Annotator.Plugin(), {
        pluginInit: function () {
            $(document).on('keyup', this.onKeyUp);
        },

        destroy: function () {
            $(document).off('keyup', this.onKeyUp);
        },

        isShortcut: function (event) {
            // Character ']' has keyCode 221
            return event.keyCode === 221 && event.ctrlKey && event.shiftKey;
        },

        hasSelection: function (ranges) {
            return (ranges || []).length;
        },

        saveSelection: function () {
            this.savedRange = Annotator.Util.getGlobal().getSelection().getRangeAt(0);
        },

        restoreSelection: function () {
            if (this.savedRange) {
                var browserRange = new Annotator.Range.BrowserRange(this.savedRange),
                    normedRange = browserRange.normalize().limit(this.annotator.wrapper[0]);

                Annotator.Util.readRangeViaSelection(normedRange);
                this.savedRange = null;
            }
        },

        onKeyUp: function (event) {
            var annotator = this.annotator,
                self = this,
                isAnnotator, annotation, highlights, position, save, cancel, cleanup;

            // Do nothing if not a shortcut.
            if (!this.isShortcut(event)) {
                return true;
            }
            // Get the currently selected ranges.
            annotator.selectedRanges = annotator.getSelectedRanges();
            // Do nothing if there is no selection
            if (!this.hasSelection(annotator.selectedRanges)) {
                return true;
            }

            isAnnotator = _.some(annotator.selectedRanges, function (range) {
                return annotator.isAnnotator(range.commonAncestor);
            });

            // Do nothing if we are in Annotator.
            if (isAnnotator) {
                return true;
            }
            // Show a temporary highlight so the user can see what they selected
            // Also extract the quotation and serialize the ranges
            annotation = annotator.setupAnnotation(annotator.createAnnotation());
            highlights = $(annotation.highlights).addClass('annotator-hl-temporary');

            if (annotator.adder.is(':visible')) {
                position = annotator.adder.position();
                annotator.adder.hide();
            } else {
                position = highlights.last().position();
            }

            // Subscribe to the editor events
            // Make the highlights permanent if the annotation is saved
            save = function () {
                cleanup();
                highlights.removeClass('annotator-hl-temporary');
                // Fire annotationCreated events so that plugins can react to them
                annotator.publish('annotationCreated', [annotation]);
            };

            // Remove the highlights if the edit is cancelled
            cancel = function () {
                self.restoreSelection();
                cleanup();
                annotator.deleteAnnotation(annotation);
            };

            // Don't leak handlers at the end
            cleanup = function () {
                annotator.unsubscribe('annotationEditorHidden', cancel);
                annotator.unsubscribe('annotationEditorSubmit', save);
                self.savedRange = null;
            };

            annotator.subscribe('annotationEditorHidden', cancel);
            annotator.subscribe('annotationEditorSubmit', save);

            this.saveSelection();
            // Display the editor.
            annotator.showEditor(annotation, position);
            event.preventDefault();
        }
    });
});
}).call(this, define || RequireJS.define);
