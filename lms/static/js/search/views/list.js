var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.List = Backbone.View.extend({
        el: '#search-content',
        $courseContent: $('#course-content'),
        events: {
            'click .search-load-next': 'loadNext'
        },

        listTemplate: _.template($('#search_list-tpl').html()),
        loadingTemplate: _.template($('#search_loading-tpl').html()),

        initialize: function () {
            this.collection.on('search', this.render, this);
            this.collection.on('next', this.renderNext, this);
            // this.collection.on('error', ???, this);
        },

        render: function () {
            this.$el.html(this.listTemplate({
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
            var listHtml = this.renderItems();
            if (! this.collection.hasNextPage()) {
                this.$el.find('.search-load-next').remove();
            }
            this.$el.find('.icon-spin').hide();
        },

        renderItems: function () {
            var items = [];
            _.each(this.collection.models, function (model) {
                var item = new edx.search.Item({ model: model });
                items.push(item.render().el);
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

        loadNext: function (event) {
            event.preventDefault();
            this.$el.find('.icon-spin').show();
            this.trigger('next');
        }

    });

})(jQuery, _, Backbone, gettext);
