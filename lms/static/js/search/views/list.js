var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict';

    edx.search = edx.search || {};

    edx.search.List = Backbone.View.extend({
        el: '#search-content',
        events: {
            'click .search-load-next': 'loadNext'
        },

        initialize: function () {
            this.courseName = this.$el.attr('data-course-name');
            this.$courseContent = $('#course-content');
            this.listTemplate = _.template($('#search_list-tpl').html());
            this.loadingTemplate = _.template($('#search_loading-tpl').html());
            this.errorTemplate = _.template($('#search_error-tpl').html());
            this.collection.on('search', this.render, this);
            this.collection.on('next', this.renderNext, this);
            this.collection.on('error', this.showErrorMessage, this);
        },

        render: function () {
            this.$el.html(this.listTemplate({
                courseName: this.courseName,
                totalCount: this.collection.totalCount,
                pageSize: this.collection.pageSize,
                hasMoreResults: this.collection.hasNextPage()
            }));
            this.renderItems();
            this.$courseContent.hide();
            this.$el.show();
            return this;
        },

        renderNext: function () {
            // total count may have changed
            this.$el.find('.search-count-total').text(this.collection.totalCount);
            this.renderItems();
            if (! this.collection.hasNextPage()) {
                this.$el.find('.search-load-next').remove();
            }
            this.$el.find('.icon-spin').hide();
        },

        renderItems: function () {
            var items = this.collection.map(function (result) {
                var item = new edx.search.Item({ model: result });
                return item.render().el;
            });
            this.$el.find('.search-results').append(items);
        },

        clear: function () {
            this.$el.hide().empty();
            this.$courseContent.show();
        },

        showLoadingMessage: function () {
            this.$el.html(this.loadingTemplate());
            this.$el.show();
            this.$courseContent.hide();
        },

        showErrorMessage: function () {
            this.$el.html(this.errorTemplate());
            this.$el.show();
            this.$courseContent.hide();
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.$el.find('.icon-spin').show();
        }

    });

})(jQuery, _, Backbone, gettext);
