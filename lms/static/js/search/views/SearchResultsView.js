var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.SearchResultsView = Backbone.View.extend({
        el: '#search-content',
        tpl: '#search_result_list-tpl',
        itemTpl: '#search_result_item-tpl',

        initialize: function (options) {
            this.tpl = $(this.tpl).html();
            this.itemTpl = $(this.itemTpl).html();
            this.collection = options.collection || {};
            this.collection.on('change reset add remove', this.render, this);
            this.$courseContent = $('#course-content')
        },

        renderItem: function (searchItem) {
            var item = searchItem.attributes;
            item.locationPathString = '';
            _.each(_.keys(item.location).sort(), function(key, i, list) {
                item.locationPathString += item.location[key];
                if (i + 1 < list.length) {
                    item.locationPathString += ' ▸ ';
                }
            });
            return _.template(this.itemTpl, { item: item });
        },

        render: function () {
            if (_.isEmpty(this.collection.models)) {
                this.renderEmptyMessage();
            }
            else {
                this.renderSearchResults();
            }
            this.$courseContent.hide();
            this.$el.show();
        },

        renderEmptyMessage: function () {

        },

        renderSearchResults: function () {
            var self = this;
            var listHtml = '';
            _.each(self.collection.models, function (searchItem) {
                listHtml += self.renderItem(searchItem);
            });
            self.$el.html(_.template(self.tpl, {
                totalCount: self.collection.totalCount,
                pageSize: self.collection.pageSize,
                searchResults: listHtml
            }));
            console.log('hahaha')
        },

        clearSearchResults: function () {
            this.$el.hide().empty();
            this.$courseContent.show();
        }

    });

})(jQuery, _, Backbone, gettext);
