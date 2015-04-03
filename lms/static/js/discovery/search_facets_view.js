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
        moreLessLinksTpl: '#more_less_links-tpl',

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
            this.moreLessTpl = _.template($(this.moreLessLinksTpl).html());
            this.$el.html(this.tpl());
            this.facetViews = [];
            this.$facetViewsEl = this.$el.find('.search-facets-lists');
        },

        render: function () {
            return this;
        },

        collapse: function(event) {
            var $el = $(event.currentTarget),
                $more = $el.siblings('.show-more'),
                $ul = $el.parent('div').siblings('ul');

            event.preventDefault();

            $ul.addClass('collapse');
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
            $ul.removeClass('collapse');
            $el.siblings('.show-less').removeClass('hidden');
        },

        addFacet: function(event) {
            event.preventDefault();
            var $target = $(event.currentTarget);
            var value = $target.find('.facet-option').data('value');
            var name = $target.find('.facet-option').data('text');
            var data = {type: $target.data('facet'), query: value, name: name};
            this.trigger('addFilter', data);
        },

        displayName: function(name, term){
            if(this.facetsTypes.hasOwnProperty(name)) {
                if(term) {
                    if (typeof this.facetsTypes[name].terms !== 'undefined') {
                        return this.facetsTypes[name].terms.hasOwnProperty(term) ? this.facetsTypes[name].terms[term] : term;
                    }
                    else {
                        return term;
                    }
                }
                else if(this.facetsTypes[name].hasOwnProperty('name')) {
                    return this.facetsTypes[name]['name'];
                }
                else {
                    return name;
                }
            }
            else{
                return term ? term : name;
            }
        },

        renderFacets: function(facets) {
            var self = this;
            // Remove old facets
            $.each(this.facetViews, function(key, facetsList) {
                facetsList.remove();
            });
            self.facetViews = [];
            // Render new facets
            $.each(facets, function(name, stats) {
                var facetsView = new FacetsView();
                self.facetViews.push(facetsView);
                self.$facetViewsEl.append(facetsView.render(name, self.displayName(name), stats).el);
                $.each(stats.terms, function(term, count) {
                    var facetView = new FacetView();
                    facetsView.$views.append(facetView.render(name, self.displayName(name, term), term, count).el);
                    facetsView.list.push(facetView);
                });
                if(_.size(stats.terms) > 9) {
                    facetsView.$el.append(self.moreLessTpl());
                }
            });
        }

    });

});

})(define || RequireJS.define);
