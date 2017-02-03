(function(define) {
    define([
        'jquery',
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, HtmlUtils) {
        'use strict';

        return Backbone.View.extend({

            el: '.search-facets',
            events: {
                'click li button': 'selectOption',
                'click .show-less': 'collapse',
                'click .show-more': 'expand'
            },

            initialize: function(options) {
                this.meanings = options.meanings || {};
                this.$container = this.$el.find('.search-facets-lists');
                this.facetTpl = HtmlUtils.template($('#facet-tpl').html());
                this.facetOptionTpl = HtmlUtils.template($('#facet_option-tpl').html());
            },

            facetName: function(key) {
                return this.meanings[key] && this.meanings[key].name || key;
            },

            termName: function(facetKey, termKey) {
                return this.meanings[facetKey] &&
                this.meanings[facetKey].terms &&
                this.meanings[facetKey].terms[termKey] || termKey;
            },

            renderOptions: function(options) {
                return HtmlUtils.joinHtml.apply(this, _.map(options, function(option) {
                    var data = _.clone(option.attributes);
                    data.name = this.termName(data.facet, data.term);
                    return this.facetOptionTpl(data);
                }, this));
            },

            renderFacet: function(facetKey, options) {
                return this.facetTpl({
                    name: facetKey,
                    displayName: this.facetName(facetKey),
                    optionsHtml: this.renderOptions(options),
                    listIsHuge: (options.length > 9)
                });
            },

            render: function() {
                var grouped = this.collection.groupBy('facet');
                var htmlSnippet = HtmlUtils.joinHtml.apply(
                this, _.map(grouped, function(options, facetKey) {
                    if (options.length > 0) {
                        return this.renderFacet(facetKey, options);
                    }
                }, this)
            );
                HtmlUtils.setHtml(this.$container, htmlSnippet);
                return this;
            },

            collapse: function(event) {
                var $el = $(event.currentTarget),
                    $more = $el.siblings('.show-more'),
                    $ul = $el.parent().siblings('ul');

                $ul.addClass('collapse');
                $el.addClass('hidden');
                $more.removeClass('hidden');
            },

            expand: function(event) {
                var $el = $(event.currentTarget),
                    $ul = $el.parent('div').siblings('ul');

                $el.addClass('hidden');
                $ul.removeClass('collapse');
                $el.siblings('.show-less').removeClass('hidden');
            },

            selectOption: function(event) {
                var $target = $(event.currentTarget);
                this.trigger(
                'selectOption',
                $target.data('facet'),
                $target.data('value'),
                $target.data('text')
            );
            }

        });
    });
})(define || RequireJS.define);
