;(function (define, undefined) {
'use strict';
define(['jquery', 'underscore', 'annotator'], function ($, _, Annotator) {
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
        $.fn.addBack = function(selector) {
            return this.add(selector === null ?
                    this.prevObject : this.prevObject.filter(selector)
            );
        };
    }

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

    /**
     * Modifies Annotator.highlightRange to add a "tabindex=0" attribute
     * to the <span class="annotator-hl"> markup that encloses the note.
     * These are then focusable via the TAB key.
     **/
    Annotator.prototype.highlightRange = _.compose(
        function (results) {
            $('.annotator-hl', this.wrapper).attr('tabindex', 0);
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
                _.invoke(Annotator._instances, 'unfreeze');
            } else {
                // Unfreeze only this instance and unbound associated 'click.edxnotes:freeze' handler
                $(document).off('click.edxnotes:freeze' + this.uid);
                this.isFrozen = false;
            }

            if (this.logger && this.logger.destroy) {
                this.logger.destroy();
            }
        }
    );

    /**
     * Modifies Annotator.Viewer.html.item template to add an i18n for the
     * buttons.
     **/
    Annotator.Viewer.prototype.html.item = [
        '<li class="annotator-annotation annotator-item">',
          '<span class="annotator-controls">',
            '<a href="#" title="', _t('View as webpage'), '" class="annotator-link">',
                _t('View as webpage'),
            '</a>',
            '<button title="', _t('Edit'), '" class="annotator-edit">',
                _t('Edit'),
            '</button>',
            '<button title="', _t('Delete'), '" class="annotator-delete">',
                _t('Delete'),
            '</button>',
          '</span>',
        '</li>'
    ].join('');

    $.extend(true, Annotator.prototype, {
        events: {
            '.annotator-hl click': 'onHighlightClick',
            '.annotator-viewer click': 'onNoteClick'
        },

        isFrozen: false,
        uid: _.uniqueId(),

        onHighlightClick: function (event) {
            Annotator.Util.preventEventDefault(event);

            if (!this.isFrozen) {
                event.stopPropagation();
                this.onHighlightMouseover.call(this, event);
            }
            Annotator.frozenSrc = this;
            _.invoke(Annotator._instances, 'freeze');
        },

        onNoteClick: function (event) {
            event.stopPropagation();
            Annotator.Util.preventEventDefault(event);
            if (!$(event.target).is('.annotator-delete')) {
                Annotator.frozenSrc = this;
                _.invoke(Annotator._instances, 'freeze');
            }
        },

        freeze: function() {
            if (!this.isFrozen) {
                // Remove default events
                this.removeEvents();
                this.viewer.element.unbind('mouseover mouseout');
                this.uid = _.uniqueId();
                $(document).on('click.edxnotes:freeze'+this.uid, this.unfreeze.bind(this));
                this.isFrozen = true;
            }
        },

        unfreeze: function() {
            if (this.isFrozen) {
                // Add default events
                this.addEvents();
                this.viewer.element.bind({
                    'mouseover': this.clearViewerHideTimer,
                    'mouseout':  this.startViewerHideTimer
                });
                this.viewer.hide();
                $(document).off('click.edxnotes:freeze'+this.uid);
                this.isFrozen = false;
                Annotator.frozenSrc = null;
            }
        }
    });
});
}).call(this, define || RequireJS.define);
