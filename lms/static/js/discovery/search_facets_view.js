;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext'
], function ($, _, Backbone, gettext) {
    'use strict';

    return Backbone.View.extend({

        el: '.search-facets',

        tagName: 'div',
        templateId: '#search_facets-tpl',
        className: 'facets',

        events: {
            'click li': 'addFacet',
            'click .show-less': 'collapse',
            'click .show-more': 'expand',
        },

        initialize: function () {
            // Empty for now.
        },

        render: function () {
            // Empty for now.
        },

        collapse: function(event) {
            var $el = $(event.currentTarget),
                $more = $el.siblings('.show-more'),
                $ul = $el.parent('div').siblings('ul');

            event.preventDefault();

            $ul.css('max-height', '').addClass('collapse');
            $el.addClass('hidden');
            $more.removeClass('hidden');
        },

        expand: function(event) {
            var $el = $(event.currentTarget),
                $ul = $el.parent('div').siblings('ul'),
                facets = $ul.find('li').length,
                itemHeight = 34;

            event.preventDefault();

            $el.addClass('hidden');
            $ul.removeClass('collapse').css('max-height', facets * itemHeight + 'px');
            $el.siblings('.show-less').removeClass('hidden');
        },

        addFacet: function(event) {
            event.preventDefault();
            var $target = $(event.currentTarget);
            var value = $target.find('.facet-option').data('value');
            var data = {type: $target.data('facet'), query: value};
            this.trigger('addFilter', data);
        }

    });

});

})(define || RequireJS.define);
