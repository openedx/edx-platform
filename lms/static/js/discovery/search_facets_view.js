;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/discovery/facets_view',
    'js/discovery/facet_view'
], function ($, _, Backbone, gettext, FacetsView, FacetView) {
    'use strict';

    return Backbone.View.extend({

        el: '.search-facets',

        tagName: 'div',
        templateId: '#search_facets_list-tpl',
        className: 'facets',
        facetsTypes: {},

        events: {
            'click li': 'addFacet',
            'click .show-less': 'collapse',
            'click .show-more': 'expand',
        },

        initialize: function (facetsTypes) {
            if(facetsTypes) {
                this.facetsTypes = facetsTypes;
            }
            this.tpl = _.template($(this.templateId).html());
            this.$el.html(this.tpl());
            this.facetViews = [];
            this.$facetViewsEl = this.$el.find('.search-facets-lists');
        },

        render: function () {

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
        },

        renderFacets: function(facets) {
            var self = this;
            // Remove old facets
            $.each(this.facetViews, function(key, facets) {
                facets.remove();
            });
            // Render new facets
            $.each(facets, function(name, stats) {
                var facetsView = new FacetsView();
                self.facetViews.push(facetsView);
                var displayName = name;
                if(self.facetsTypes.hasOwnProperty(name)) {
                    displayName = self.facetsTypes[name];
                }
                self.$facetViewsEl.append(facetsView.render(name, displayName, stats).el);
                $.each(stats.terms, function(term, count) {
                    var facetView = new FacetView();
                    facetsView.$views.append(facetView.render(name, term, count).el);
                    facetsView.list.push(facetView);
                });
            });
        }

    });

});

})(define || RequireJS.define);
