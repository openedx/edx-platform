;(function (define, undefined) {
'use strict';
define([
    'jquery', 'underscore', 'annotator_1.2.9', 'js/edxnotes/utils/utils'
], function ($, _, Annotator, Utils) {
    var _t = Annotator._t;

    /**
     * We currently run JQuery 1.7.2 in Jasmine tests and LMS.
     * AnnotatorJS 1.2.9. uses two calls to addBack (in the two functions
     * 'isAnnotator' and 'onHighlightMouseover') which was only defined in
     * JQuery 1.8.0. In LMS, it works without throwing an error because
     * JQuery.UI 1.10.0 adds support to jQuery<1.8 by augmenting '$.fn' with
     * that missing function. It is not the case for all Jasmine unit tests,
     * so we add it here if necessary.
     **/
    if (!$.fn.addBack) {
        $.fn.addBack = function (selector) {
            return this.add(
                selector === null ? this.prevObject : this.prevObject.filter(selector)
            );
        };
    }

    /**
     * The original _setupDynamicStyle uses a very expensive call to
     * Util.maxZIndex(...) that sets the z-index of .annotator-adder,
     * .annotator-outer, .annotator-notice, .annotator-filter. We set these
     * values in annotator.min.css instead and do nothing here.
     */
    Annotator.prototype._setupDynamicStyle = function() { };

    Annotator.frozenSrc = null;

    /**
     * Modifies Annotator.Plugin.Auth.haveValidToken to make it work with a new
     * token format.
     **/
    Annotator.Plugin.Auth.prototype.haveValidToken = function() {
        return (
            this._unsafeToken &&
            this._unsafeToken.sub &&
            this._unsafeToken.exp &&
            this._unsafeToken.iat &&
            this.timeToExpiry() > 0
        );
    };

    /**
     * Modifies Annotator.Plugin.Auth.timeToExpiry to make it work with a new
     * token format.
     **/
    Annotator.Plugin.Auth.prototype.timeToExpiry = function() {
        var now = new Date().getTime() / 1000,
            expiry = this._unsafeToken.exp,
            timeToExpiry = expiry - now;

        return (timeToExpiry > 0) ? timeToExpiry : 0;
    };


    Annotator.Plugin.Tags.prototype.updateField = _.compose(
        function() {
            // Add screen reader label for edit mode. Note that the id of the tags element will not always be "1".
            // It depends on the number of annotatable components on the page.
            var tagsField = $("li.annotator-item >input", this.annotator.editor.element).attr('id');
            if ($("label.sr[for='"+ tagsField + "']", this.annotator.editor.element).length === 0) {
                $('<label class="sr" for='+ tagsField +'>' + _t('Tags (space-separated)') + '</label>').insertBefore(
                    $('#'+tagsField, this.annotator.editor.element)
                );
            }
            return this;
        },
        Annotator.Plugin.Tags.prototype.updateField
    );

    Annotator.Plugin.Tags.prototype.updateViewer = _.compose(
        function() {
            // Add ARIA information for viewing mode.
            $('div.annotator-tags', this.wrapper).attr({
                'role': 'region',
                'aria-label': 'tags'
            });
            return this;
        },
        Annotator.Plugin.Tags.prototype.updateViewer
    );

    /**
     * Modifies Annotator.highlightRange to add "tabindex=0" and role="link"
     * attributes to the <span class="annotator-hl"> markup that encloses the
     * note. These are then focusable via the TAB key and are accessible to
     * screen readers.
     **/
    Annotator.prototype.highlightRange = _.compose(
        function (results) {
            $('.annotator-hl', this.wrapper).attr({
                'tabindex': 0,
                'role': 'link'
            });
            return results;
        },
        Annotator.prototype.highlightRange
    );

    /**
     * Modifies Annotator.destroy to unbind click.edxnotes:freeze from the
     * document and reset isFrozen to default value, false.
     **/
    Annotator.prototype.destroy = _.compose(
        Annotator.prototype.destroy,
        function () {
            // We are destroying the instance that has the popup visible, revert to default,
            // unfreeze all instances and set their isFrozen to false
            if (this === Annotator.frozenSrc) {
                this.unfreezeAll();
            } else {
                // Unfreeze only this instance and unbound associated 'click.edxnotes:freeze' handler
                $(document).off('click.edxnotes:freeze' + this.uid);
                this.isFrozen = false;
            }

            if (this.logger && this.logger.destroy) {
                this.logger.destroy();
            }
            // Unbind onNoteClick from click
            this.viewer.element.off('click', this.onNoteClick);
            this.wrapper.off('click', '.annotator-hl');
        }
    );

    /**
     * Modifies Annotator.Viewer.html template to make viewer div focusable.
     * Also adds a close button and necessary i18n attributes to all buttons.
    **/
        Annotator.Viewer.prototype.html = {
        element: [
            '<div class="annotator-outer annotator-viewer">',
                '<ul class="annotator-widget annotator-listing" tabindex="-1"></ul>',
            '</div>'
        ].join(''),
        item: [
            '<li class="annotator-annotation annotator-item">',
                '<span class="annotator-controls">',
                    '<a href="#" title="', _t('View as webpage'), '" class="annotator-link">',
                        _t('View as webpage'),
                    '</a>',
                    '<button class="annotator-edit">',
                        _t('Edit'),
                        '<span class="sr">', _t('Note'), '</span>',
                    '</button>',
                    '<button class="annotator-delete">',
                        _t('Delete'),
                        '<span class="sr">', _t('Note'), '</span>',
                    '</button>',
                    '<button class="annotator-close">',
                        _t('Close'),
                        '<span class="sr">', _t('Note'), '</span>',
                    '</button>',
                '</span>',
            '</li>'
        ].join('')
    };

    /**
     * Overrides Annotator._setupViewer to add a "click" event on viewer and to
     * improve line breaks.
     **/
    Annotator.prototype._setupViewer = function () {
        var self = this;
        this.viewer = new Annotator.Viewer({readOnly: this.options.readOnly});
        this.viewer.element.on('click', _.bind(this.onNoteClick, this));
        this.viewer.hide()
            .on("edit", this.onEditAnnotation)
            .on("delete", this.onDeleteAnnotation)
            .addField({
                load: function (field, annotation) {
                    if (annotation.text) {
                        $(field).html(Utils.nl2br(Annotator.Util.escape(annotation.text)));
                    } else {
                        $(field).html('<i>' + _t('No Comment') + '</i>');
                    }
                    return self.publish('annotationViewerTextField', [field, annotation]);
                }
            })
            .element.appendTo(this.wrapper).bind({
                "mouseover": this.clearViewerHideTimer,
                "mouseout":  this.startViewerHideTimer
            });
        return this;
    };

    Annotator.Editor.prototype.isShown = Annotator.Viewer.prototype.isShown;

    /**
     * Modifies Annotator.Editor.html template to add tabindex = -1 to
     * form.annotator-widget and reverse order of Save and Cancel buttons.
     **/
    Annotator.Editor.prototype.html = [
        '<div class="annotator-outer annotator-editor">',
            '<form class="annotator-widget" tabindex="-1">',
                '<ul class="annotator-listing"></ul>',
                '<div class="annotator-controls">',
                    '<button class="annotator-save">',
                        _t('Save'),
                        '<span class="sr">', _t('Note'), '</span>',
                    '</button>',
                    '<button class="annotator-cancel">',
                        _t('Cancel'),
                        '<span class="sr">', _t('Note'), '</span>',
                    '</button>',
                '</div>',
            '</form>',
        '</div>'
    ].join('');


    /**
     * Modifies Annotator.Editor.show, in the case of a keydown event, to remove
     * focus from Save button and put it on form.annotator-widget instead.
     *
     * Also add a sr label for note textarea.
     **/
    Annotator.Editor.prototype.show = _.compose(
        function (event) {
            // Add screen reader label for the note area. Note that the id of the tags element will not always be "0".
            // It depends on the number of annotatable components on the page.
            var noteField = $("li.annotator-item >textarea", this.element).attr('id');
            if ($("label.sr[for='"+ noteField + "']", this.element).length === 0) {
                $('<label class="sr" for='+ noteField +'>' + _t('Note') + '</label>').insertBefore(
                    $('#'+noteField, this.element)
                );
            }

            if (event.type === 'keydown') {
                this.element.find('.annotator-save').removeClass(this.classes.focus);
                this.element.find('form.annotator-widget').focus();
            }
        },
        Annotator.Editor.prototype.show
    );

    /**
     * Removes the textarea keydown event handler as it triggers 'processKeypress'
     * which hides the viewer on ESC and saves on ENTER. We will define different
     * behaviors for these in /plugins/accessibility.js
     **/
    delete Annotator.Editor.prototype.events["textarea keydown"];

    /**
     * Modifies Annotator.onHighlightMouseover to avoid showing the viewer if the
     * editor is opened.
     **/
    Annotator.prototype.onHighlightMouseover = _.wrap(
        Annotator.prototype.onHighlightMouseover,
        function (func, event) {
            // Do nothing if the editor is opened.
            if (this.editor.isShown()) {
                return false;
            }
            return func.call(this, event);
        },
        Annotator.prototype._setupViewer
    );

    /**
     * Modifies Annotator._setupWrapper to add a "click" event on '.annotator-hl'.
     **/
    Annotator.prototype._setupWrapper = _.compose(
        function () {
            this.element.on('click', '.annotator-hl', _.bind(this.onHighlightClick, this));
            return this;
        },
        Annotator.prototype._setupWrapper
    );

    $.extend(true, Annotator.prototype, {
        isFrozen: false,
        uid: _.uniqueId(),

        onHighlightClick: function (event) {
            event.stopPropagation();
            if (!this.editor.isShown()) {
                this.unfreezeAll();
                this.onHighlightMouseover.call(this, event);
                Annotator.frozenSrc = this;
                this.freezeAll();
            }
        },

        onNoteClick: function (event) {
            var target = $(event.target);
            event.stopPropagation();
            Annotator.Util.preventEventDefault(event);

            if (!(target.is('.annotator-delete') || target.is('.annotator-close'))) {
                Annotator.frozenSrc = this;
                this.freezeAll();
            } else if (target.is('.annotator-close')) {
                this.viewer.hide();
            }
        },

        freeze: function () {
            if (!this.isFrozen) {
                // Remove default events
                this.removeEvents();
                this.viewer.element.unbind('mouseover mouseout');
                this.uid = _.uniqueId();
                $(document).on('click.edxnotes:freeze' + this.uid, _.bind(this.unfreeze, this));
                this.isFrozen = true;
            }
            return this;
        },

        unfreeze: function () {
            if (this.isFrozen) {
                // Add default events
                this.addEvents();
                this.viewer.element.bind({
                    'mouseover': this.clearViewerHideTimer,
                    'mouseout':  this.startViewerHideTimer
                });
                this.viewer.hide();
                $(document).off('click.edxnotes:freeze' + this.uid);
                this.isFrozen = false;
                Annotator.frozenSrc = null;
            }
            return this;
        },

        freezeAll: function () {
            _.invoke(Annotator._instances, 'freeze');
            return this;
        },

        unfreezeAll: function () {
            _.invoke(Annotator._instances, 'unfreeze');
            return this;
        },

        showFrozenViewer: function (annotations, location) {
            this.showViewer(annotations, location);
            this.freezeAll();
            return this;
        }
    });
});
}).call(this, define || RequireJS.define);
