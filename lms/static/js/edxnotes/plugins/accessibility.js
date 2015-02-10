;(function (define, undefined) {
'use strict';
define(['jquery', 'underscore', 'annotator_1.2.9'], function ($, _, Annotator) {
    /**
     * Adds the Accessibility Plugin
     **/
    Annotator.Plugin.Accessibility = function () {
        _.bindAll(this,
            'addAriaAttributes', 'onHighlightKeyDown', 'onViewerKeyDown',
            'onEditorKeyDown'
        );
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
        Annotator.Plugin.apply(this, arguments);
    };

    $.extend(Annotator.Plugin.Accessibility.prototype, new Annotator.Plugin(), {
        pluginInit: function () {
            this.annotator.subscribe('annotationViewerTextField', this.addAriaAttributes);
            this.annotator.element.on('keydown.accessibility.hl', '.annotator-hl', this.onHighlightKeyDown);
            this.annotator.element.on('keydown.accessibility.viewer', '.annotator-viewer', this.onViewerKeyDown);
            this.annotator.element.on('keydown.accessibility.editor', '.annotator-editor', this.onEditorKeyDown);
            this.addTabIndex();
        },

        destroy: function () {
            this.annotator.unsubscribe('annotationViewerTextField', this.addAriaAttributes);
            this.annotator.element.off('keydown.accessibility.hl');
            this.annotator.element.off('keydown.accessibility.viewer');
            this.annotator.element.off('keydown.accessibility.editor');
        },

        addTabIndex: function () {
            this.annotator.element
                .find('.annotator-edit, .annotator-delete')
                .attr('tabindex', 0);
        },

        addAriaAttributes: function (field, annotation) {
            var ariaNoteId = 'aria-note-' + annotation.id;
            // Add ARIA attributes to highlighted text ie <span class="annotator-hl">Highlighted text</span>
            // aria-describedby refers to the actual note that was taken.
            _.each(annotation.highlights, function(highlight) {
                $(highlight).attr('aria-describedby', ariaNoteId);
            });
            // Add ARIA attributes to associated note ie <div>My note</div>
            $(field).attr({
                'tabindex': -1,
                'id': ariaNoteId,
                'role': 'note',
                'class': 'annotator-note'
            });
        },

        focusOnHighlightedText: function (event) {
            var id = this.annotator.element.find('.annotator-viewer')
                                           .find('.annotator-note')
                                           .attr('id');
            $('.annotator-hl[aria-describedby=' + id + ']').focus();
            event.preventDefault();
        },

        getViewerTabControls: function () {
            var viewer, notes, viewerControls, editButtons, delButtons, closeButtons, tabControls = [], i;

            // Viewer elements
            viewer = this.annotator.element.find('.annotator-viewer');
            notes = viewer.find('.annotator-note');
            viewerControls = viewer.find('.annotator-controls');
            editButtons = viewerControls.find('.annotator-edit');
            delButtons = viewerControls.find('.annotator-delete');
            closeButtons = viewerControls.find('.annotator-close');

            // Note and ddit, delete and close buttons always come in quadruplets
            for (i = 0; i < editButtons.length; i++) {
                tabControls.push($(notes.get(i)));
                tabControls.push($(editButtons.get(i)));
                tabControls.push($(delButtons.get(i)));
                tabControls.push($(closeButtons.get(i)));
            }

            return tabControls;
        },

        getEditorTabControls: function () {
            var editor, editorControls, textArea, save, cancel, tabControls = [];

            // Editor elements
            editor = this.annotator.element.find('.annotator-editor');
            editorControls = editor.find('.annotator-controls');
            textArea = editor.find('.annotator-listing')
                             .find('.annotator-item')
                             .first()
                             .children('textarea');
            save  = editorControls.find('.annotator-save');
            cancel = editorControls.find('.annotator-cancel');

            tabControls.push($(textArea.get(0)), $(save.get(0)), $(cancel.get(0)));

            return tabControls;
        },

        focusOnNextTabControl: function (tabControls, tabControl) {
            var nextIndex;

            _.each(tabControls, function (element, index) {
                if (element.is(tabControl)) {
                    nextIndex = index === tabControls.length - 1 ? 0 : index + 1;
                    tabControls[nextIndex].focus();
                }

            });
        },

        focusOnPreviousTabControl: function (tabControls, tabControl) {
            var previousIndex;
            _.each(tabControls, function (element, index) {
                if (element.is(tabControl)) {
                    previousIndex = index === 0  ? tabControls.length - 1 : index - 1;
                    tabControls[previousIndex].focus();
                }
            });
        },

        onHighlightKeyDown: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.currentTarget),
                annotations, position;

            switch (keyCode) {
                case KEY.ENTER:
                case KEY.SPACE:
                    if (!this.annotator.viewer.isShown()) {
                        position = target.position();
                        annotations = target.parents('.annotator-hl').addBack().map(function() {
                            return $(this).data('annotation');
                        });
                        this.annotator.showViewer($.makeArray(annotations), {top: position.top, left: position.left});
                        this.annotator.element.find('.annotator-listing').focus();
                    }
                    break;
                case KEY.ESCAPE:
                    this.annotator.viewer.hide();
                    break;
            }
            // We do not stop propagation and default behavior on a TAB keypress
            if (event.keyCode !== KEY.TAB || (event.keyCode == KEY.TAB && this.annotator.viewer.isShown())) {
                event.preventDefault();
                event.stopPropagation();
            }
        },

        onViewerKeyDown: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.target),
                listing = this.annotator.element.find('.annotator-listing'),
                tabControls;

            switch (keyCode) {
                case KEY.TAB:
                    tabControls = this.getViewerTabControls();
                    if (event.shiftKey) { // Tabbing backwards
                        if (target.is(listing)) {
                            _.last(tabControls).focus();
                        }
                        else {
                            this.focusOnPreviousTabControl(tabControls, target);
                        }
                    } else { // Tabbing forward
                        if (target.is(listing)) {
                            _.first(tabControls).focus();
                        }
                        else {
                            this.focusOnNextTabControl(tabControls, target);
                        }
                    }
                    event.preventDefault();
                    event.stopPropagation();
                    break;
                case KEY.ENTER:
                case KEY.SPACE:
                    if (target.hasClass('annotator-close')) {
                        this.annotator.viewer.hide();
                        this.focusOnHighlightedText(event);
                    }
                    break;
                case KEY.ESCAPE:
                    this.annotator.viewer.hide();
                    this.focusOnHighlightedText(event);
                    break;
            }
        },

        onEditorKeyDown: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.target),
                editor, editorControls, save, cancel,
                tabControls;

            editor = this.annotator.element.find('.annotator-editor');
            editorControls = editor.find('.annotator-controls');
            save  = editorControls.find('.annotator-save');
            cancel = editorControls.find('.annotator-cancel');

            switch (keyCode) {
                case KEY.TAB:
                    tabControls = this.getEditorTabControls();
                    if (event.shiftKey) { // Tabbing backwards
                        this.focusOnPreviousTabControl(tabControls, target);
                    } else { // Tabbing forward
                        this.focusOnNextTabControl(tabControls, target);
                    }
                    event.preventDefault();
                    event.stopPropagation();
                    break;
                case KEY.ENTER:
                    if (target.is(save) || event.metaKey || event.ctrlKey) {
                        this.annotator.editor.submit();
                    } else if (target.is(cancel)) {
                        this.annotator.editor.hide();
                    } else {
                        break;
                    }
                    this.focusOnHighlightedText(event);
                    break;
                case KEY.SPACE:
                    if (target.is(save)) {
                        this.annotator.editor.submit();
                    } else if (target.is(cancel)) {
                        this.annotator.editor.hide();
                    } else {
                        break;
                    }
                    this.focusOnHighlightedText(event);
                    break;
                case KEY.ESCAPE:
                    this.annotator.editor.hide();
                    this.focusOnHighlightedText(event);
                    break;
            }
        }
    });
});
}).call(this, define || RequireJS.define);
