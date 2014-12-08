var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.SearchResultsView = Backbone.View.extend({
        el: '#course-content',
        tpl: '#search_result_list-tpl',
        itemTpl: '#search_result_item-tpl',

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
            var self = this;
            var listHtml = '';
            _.each(self.collection.models, function (searchItem) {
                listHtml += self.renderItem(searchItem);
            });

            this.$el.html(_.template(this.tpl, {
                totalCount: this.collection.totalCount,
                pageSize: this.collection.pageSize,
                search_result_list: listHtml
            }));

        },

        initialize: function (options) {
            this.tpl = $(this.tpl).html();
            this.itemTpl = $(this.itemTpl).html();
            this.collection = options.collection || {};
            this.collection.on('change reset add remove', this.render, this);
        }

    });

})(jQuery, _, Backbone, gettext);
