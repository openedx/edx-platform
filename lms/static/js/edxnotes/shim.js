;(function (define, $, _, undefined) {
    'use strict';
    define(['annotator'], function (Annotator) {
        var _t = Annotator._t;

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
    });
}).call(this, define || RequireJS.define, jQuery, _);
