;(function (define, undefined) {
'use strict';
define(['jquery', 'underscore', 'annotator'], function ($, _, Annotator) {
    /**
     * Adds the Accessibility Plugin
     **/
    Annotator.Plugin.Accessibility = function () {
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
        Annotator.Plugin.apply(this, arguments);
    };

    $.extend(Annotator.Plugin.Accessibility.prototype, new Annotator.Plugin(), {
        pluginInit: function () {
            this.annotator.subscribe('annotationViewerTextField', _.bind(this.addAriaAttributes, this));
            this.annotator.element.on('keydown', '.annotator-hl', _.bind(this.onHighlightKeyDown, this));
            this.annotator.element.on('keydown', '.annotator-viewer', _.bind(this.onViewerKeyDown, this));
            this.annotator.element.on('keydown', '.annotator-editor', _.bind(this.onEditorKeyDown, this));
            this.addTabIndex();
        },

        destroy: function () {
            this.annotator.unsubscribe('annotationViewerTextField', this.addAriaAttributes);
            this.annotator.element.off('keydown', '.annotator-hl');
            this.annotator.element.off('keydown', '.annotator-viewer');
            this.annotator.element.off('keydown', '.annotator-editor');
        },

        addTabIndex: function () {
            var controls, edit, del;
            controls = this.annotator.element.find('.annotator-controls');
            edit = controls.find('.annotator-edit');
            edit.attr('tabindex', 0);
            del = controls.find('.annotator-delete');
            del.attr('tabindex', 0);
        },

        addAriaAttributes: function (field, annotation) {
            var ariaNoteId = 'aria-note-' + annotation.id;
            // Add ARIA attributes to highlighted text ie <span class="annotator-hl">Highlighted text</span>
            // tabindex is set to 0 to make the span focusable via the TAB key.
            // aria-describedby refers to the actual note that was taken.
            _.each(annotation.highlights, function(highlight) {
                $(highlight).attr('aria-describedby', ariaNoteId);
            });
            // Add ARIA attributes to associated note ie <div>My note</div>
            $(field).attr({
                'id': ariaNoteId,
                'role': 'note',
                'aria-label': 'Note'
            });
        },

        focusOnHighlightedText: function (event) {
            var viewer, viewerControls, note, id;

            viewer = this.annotator.element.find('.annotator-viewer');
            viewerControls = viewer.find('.annotator-controls');
            note = viewerControls.siblings('div[role="note"]');
            id = note.attr('id');
            $('.annotator-hl[aria-describedby=' + id + ']').focus();
            event.preventDefault();
        },

        getViewerTabControls: function () {
            var viewer, viewerControls, editButtons, delButtons, tabControls = [], i;

            // Viewer elements
            viewer = this.annotator.element.find('.annotator-viewer');
            viewerControls = viewer.find('.annotator-controls');
            editButtons = viewerControls.find('.annotator-edit');
            delButtons = viewerControls.find('.annotator-delete');

            // Edit and delete buttons always come in pairs
            for (i = 0; i < editButtons.length; i++) {
                tabControls.push($(editButtons.get(i)));
                tabControls.push($(delButtons.get(i)));
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
            var KEY = $.extend($.ui.keyCode, {'n': 78}),
                keyCode = event.keyCode,
                target = $(event.currentTarget),
                annotations, position,
                controls, edit;

            switch (keyCode) {
                case KEY.TAB:
                    if (this.annotator.viewer.isShown()) {
                        controls = this.annotator.element.find('.annotator-controls');
                        edit = controls.find('.annotator-edit').first();
                        edit.focus();
                    }
                    break;
                case KEY.ENTER:
                case KEY.SPACE:
                    if (!this.annotator.viewer.isShown()) {
                        position = target.position();
                        annotations = target.parents('.annotator-hl').addBack().map(function() {
                            return $(this).data('annotation');
                        });
                        this.annotator.showViewer($.makeArray(annotations), {top: position.top, left: position.left});
                    }
                    break;
                case KEY.ESCAPE:
                    this.annotator.viewer.hide();
                    break;
                // Gives focus to the show/hide notes button
                case KEY.n:
                    if (event.ctrlKey && event.altKey)  {
                        $('.action-toggle-notes').focus();
                    }
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
                tabControls;

            switch (keyCode) {
                case KEY.TAB:
                    tabControls = this.getViewerTabControls();
                    if (event.shiftKey) { // Tabbing backwards
                        this.focusOnPreviousTabControl(tabControls, target);
                    } else { // Tabbing forward
                        this.focusOnNextTabControl(tabControls, target);
                    }
                    event.preventDefault();
                    event.stopPropagation();
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
