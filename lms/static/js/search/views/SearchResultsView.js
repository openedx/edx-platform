var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.SearchResultsView = Backbone.View.extend({
        el: '#search-content',
        events: {
            'click .search-load-next': 'loadNext'
        },
        tpl: {
            view: '#search_view-tpl',
            loading: '#search_loading-tpl',
            list: '#search_result_list-tpl'
        },

        initialize: function (options) {
            for (var key in this.tpl) {
                this.tpl[key] = $(this.tpl[key]).html();
            }
            this.collection = options.collection || {};
            this.collection.on('searchRequest', this.renderLoadingMessage, this);
            this.collection.on('search', this.renderInitial, this);
            this.collection.on('next', this.renderNextPage, this);
            this.$courseContent = $('#course-content');
        },

        renderInitial: function () {
            var listHtml = this.renderSearchList();
            this.$el.html(_.template(this.tpl.view, {
                totalCount: this.collection.totalCount,
                pageSize: this.collection.pageSize,
                hasMoreResults: this.collection.hasMoreResults(),
                list: listHtml
            }));
        },

        renderNextPage: function () {
            var listHtml = this.renderSearchList();
            if (! this.collection.hasMoreResults()) {
                this.$el.find('.search-load-next').remove();
            }
            this.$el.find('.search-results').append(listHtml);
            this.$el.find('.icon-spin').hide();
        },

        renderSearchList: function () {
            var self = this;
            var list = _.map(this.collection.models, function (model) {
                return model.attributes;
            });
            return _.template(this.tpl.list, {
                items: list,
                stringifyLocation: this.stringifyLocation
            });
        },

        renderLoadingMessage: function () {
            this.$courseContent.hide();
            this.$el.html(_.template(this.tpl.loading)).show();
        },

        clearSearchResults: function () {
            this.$el.hide().empty();
            this.$courseContent.show();
        },

        loadNext: function (event) {
            event.preventDefault();
            this.$el.find('.icon-spin').show();
            this.collection.loadNextPage();
        },

        stringifyLocation: function (location) {
            var locationString = '';
            _.each(_.keys(location).sort(), function(key, i, list) {
                locationString += location[key];
                if (i + 1 < list.length) {
                    locationString += ' ▸ ';
                }
            });
            return locationString;
        },

    });

})(jQuery, _, Backbone, gettext);
