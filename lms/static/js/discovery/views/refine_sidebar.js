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
        events: {
            'click li button': 'selectOption',
            'click .show-less': 'collapse',
            'click .show-more': 'expand'
        },

        initialize: function (options) {
            this.meanings = options.meanings || {}
            this.$container = this.$el.find('.search-facets-lists');
            this.facetTpl = _.template($('#facet-tpl').html());
            this.facetOptionTpl = _.template($('#facet_option-tpl').html());
        },

        facetName: function (key) {
            return this.meanings[key] && this.meanings[key].name || key;
        },

        termName: function (facetKey, termKey) {
            return this.meanings[facetKey] &&
                this.meanings[facetKey].terms  &&
                this.meanings[facetKey].terms[termKey] || termKey;
        },

        renderOptions: function (options) {
            var html = _.map(options, function(option) {
                var data = _.clone(option.attributes);
                data.name = this.termName(data.facet, data.term);
                return this.facetOptionTpl(data);
            }, this).join('');
            return html;
        },

        renderFacet: function (facetKey, options) {
            return this.facetTpl({
                name: facetKey,
                displayName: this.facetName(facetKey),
                options: this.renderOptions(options),
                listIsHuge: (options.length > 9)
            });
        },

        render: function () {
            var grouped = this.collection.groupBy('facet');
            var html = _.map(grouped, function(options, facetKey) {
                if (options.length > 0) {
                    return this.renderFacet(facetKey, options);
                }
            }, this).join('');
            this.$container.html(html);
            return this;
        },

        collapse: function (event) {
            var $el = $(event.currentTarget),
                $more = $el.siblings('.show-more'),
                $ul = $el.parent().siblings('ul');

            $ul.addClass('collapse');
            $el.addClass('hidden');
            $more.removeClass('hidden');
        },

        expand: function (event) {
            var $el = $(event.currentTarget),
                $ul = $el.parent('div').siblings('ul');

            $el.addClass('hidden');
            $ul.removeClass('collapse');
            $el.siblings('.show-less').removeClass('hidden');
        },

        selectOption: function (event) {
            var $target = $(event.currentTarget);
            this.trigger(
                'selectOption',
                $target.data('facet'),
                $target.data('value'),
                $target.data('text')
            );
        },

    });

});

})(define || RequireJS.define);
