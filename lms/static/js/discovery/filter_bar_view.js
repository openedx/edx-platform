;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/discovery/filters',
    'js/discovery/filter',
    'js/discovery/filter_view'
], function ($, _, Backbone, gettext, FiltersCollection, Filter, FilterView) {
    'use strict';

    return Backbone.View.extend({

        el: '#filter-bar',

        tagName: 'div',
        templateId: '#filter_bar-tpl',
        className: 'filters hidden',

        events: {
            'click #clear-all-filters': 'clearAll',
            'click li .discovery-button': 'clearFilter'
        },

        initialize: function () {
            this.collection = new FiltersCollection([]);
            this.tpl = _.template($(this.templateId).html());
            this.$el.html(this.tpl());
            this.hideClearAllButton();
            this.filtersList = this.$el.find('ul');
        },

        render: function () {
            return this;
        },

        changeQueryFilter: function(query) {
            var queryModel = this.collection.getQueryModel();
            if (typeof queryModel !== 'undefined') {
                this.collection.remove(queryModel);
            }

            if (query) {
                var data = {query: query, type: 'search_string'};
                this.addFilter(data);
            }
            else {
                this.startSearch();
            }
        },

        addFilter: function(data) {
            var currentfilter = this.collection.findWhere(data);
            if(typeof currentfilter === 'undefined') {
                var filter = new Filter(data);
                var filterView = new FilterView({model: filter});
                this.collection.add(filter);
                this.filtersList.append(filterView.render().el);
                this.trigger('search', this.getSearchTerm(), this.collection);
                if (this.$el.hasClass('hidden')) {
                    this.showClearAllButton();
                }
            }
        },

        clearFilter: function (event) {
            event.preventDefault();
            var $target =  $(event.currentTarget);
            var clearModel = this.collection.findWhere({
                query: $target.data('value'),
                type: $target.data('type')
            });
            this.collection.remove(clearModel);
            this.startSearch();
        },

        clearFilters: function() {
            this.collection.reset([]);
            this.filtersList.empty();
        },

        clearAll: function(event) {
            event.preventDefault();
            this.clearFilters();
            this.trigger('clear');
        },

        showClearAllButton: function () {
            this.$el.removeClass('hidden');
        },

        hideClearAllButton: function() {
            this.$el.addClass('hidden');
        },

        getSearchTerm: function() {
            var queryModel = this.collection.getQueryModel();
            if (typeof queryModel !== 'undefined') {
                return queryModel.get('query');
            }
            return '';
        },

        startSearch: function() {
            if (this.collection.length === 0) {
                this.trigger('clear');
            }
            else {
                this.trigger('search', this.getSearchTerm(), this.collection);
            }
        }

    });

});

})(define || RequireJS.define);
