;(function (define, undefined) {
'use strict';
define(['jquery', 'underscore', 'annotator'], function ($, _, Annotator) {

    /**
     * Modifies Annotator.deleteAnnotation to make it remove focus grabbers.
     */
    Annotator.prototype.deleteAnnotation = _.wrap(
        Annotator.prototype.deleteAnnotation,
        function (func, annotation) {
            var grabberId = $(annotation.highlights[0]).data('grabber-id');
            $('#' + grabberId).remove();
            func.call(this, annotation);
        }
    );

    /**
     * Adds the Accessibility Plugin
     **/
    Annotator.Plugin.Accessibility = function () {
        _.bindAll(this,
            'addAriaAttributes', 'onHighlightKeyDown', 'onViewerKeyDown',
            'onEditorKeyDown', 'addTabIndexHighlights'
        );
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
        Annotator.Plugin.apply(this, arguments);
    };

    $.extend(Annotator.Plugin.Accessibility.prototype, new Annotator.Plugin(), {
        events: {
            '.annotator-hl focus': 'onGrabberFocus',
            '.annotator-hl blur': 'onGrabberBlur'
        },

        pluginInit: function () {
            this.annotator.subscribe('annotationViewerTextField', this.addAriaAttributes);
            this.annotator.element.on('keydown', '.annotator-hl', this.onHighlightKeyDown);
            this.annotator.element.on('keydown', '.annotator-viewer', this.onViewerKeyDown);
            this.annotator.element.on('keydown', '.annotator-editor', this.onEditorKeyDown);
            this.annotator.subscribe('annotationsLoaded', this.addTabIndexHighlights);
            this.annotator.subscribe('annotationCreated', this.addTabIndexHighlights);
            this.addTabIndexAnnotator();
        },

        destroy: function () {
            this.annotator.unsubscribe('annotationViewerTextField', this.addAriaAttributes);
            this.annotator.unsubscribe('annotationsLoaded', this.addTabIndexHighlights);
            this.annotator.unsubscribe('annotationCreated', this.addTabIndexHighlights);
            this.annotator.element.off('keydown', '.annotator-hl');
            this.annotator.element.off('keydown', '.annotator-viewer');
            this.annotator.element.off('keydown', '.annotator-editor');
        },

        addTabIndexAnnotator: function () {
            this.annotator.viewer.element
                .find('.annotator-edit, .annotator-delete')
                .attr('tabindex', 0);
        },

        addTabIndexHighlights: function (annotations) {
            if (!_.isArray(annotations)) {
                annotations = [annotations];
            }

            _.each(annotations, function (annotation) {
                var id = annotation.id || _.uniqueId(),
                    grabber = $('<span />', {
                        'class': 'annotator-hl',
                        'id': 'note-focus-grabber-' + id,
                        'tabindex': 0,
                        'aria-labelledby': 'note-label-' + id
                    }).data('annotation', annotation);

                this.annotator.wrapper.after($('<div />', {
                    'class': 'note-label sr',
                    'id': 'note-label-' + id,
                    'text': Annotator.Util.escape(annotation.quote)
                }));

                $(annotation.highlights[0])
                    .before(grabber)
                    .data('grabber-id', 'note-focus-grabber-' + id);

            }, this);
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

        getViewerTabControls: function (event) {
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
                        annotations = $.makeArray(target.data('annotation'));
                        this.annotator.showViewer(annotations, {top: position.top, left: position.left});
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
                editor, editorControls, listing, items, firstItem, save, cancel;

            // Editor elements
            editor = this.annotator.element.find('.annotator-editor');
            listing = editor.find('.annotator-listing');
            editorControls = editor.find('.annotator-controls');
            items = listing.find('.annotator-item');
            firstItem = items.first();
            save  = editorControls.find('.annotator-save');
            cancel = editorControls.find('.annotator-cancel');

            switch (keyCode) {
                case KEY.TAB:
                    if (target.is(firstItem.children('textarea')) && event.shiftKey) {
                        cancel.focus();
                        event.preventDefault();
                        event.stopPropagation();
                    } else if (target.is(cancel) && !event.shiftKey) {
                        firstItem.children('textarea').focus();
                        event.preventDefault();
                        event.stopPropagation();
                    }
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
        },

        onGrabberFocus: function (event) {
            event.preventDefault();
            var highlights = $(event.target).data('annotation').highlights;
            $(highlights).find('.annotator-hl').andSelf().addClass('is-focused');
        },

        onGrabberBlur: function (event) {
            event.preventDefault();
            var highlights = $(event.target).data('annotation').highlights;
            $(highlights).find('.annotator-hl').andSelf().removeClass('is-focused');
        }
    });
});
}).call(this, define || RequireJS.define);
