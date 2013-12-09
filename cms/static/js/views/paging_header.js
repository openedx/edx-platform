define(["backbone", "underscore", "gettext"], function(Backbone, _, gettext) {

    var PagingHeader = Backbone.View.extend({
        initialize: function(arguments) {
            var view = arguments.view,
                collection = view.collection;
            this.view = view;
            this.template = _.template($("#paging-header-tpl").text());
            collection.bind('add', _.bind(this.render, this));
            collection.bind('remove', _.bind(this.render, this));
            collection.bind('reset', _.bind(this.render, this));
        },

        render: function() {
            var view = this.view,
                collection = view.collection,
                messageHtml = this.messageHtml();
            this.$el.html(this.template({
                messageHtml: messageHtml
            }));
            return this;
        },

        messageHtml: function() {
            var view = this.view,
                collection = view.collection,
                currentPage = collection.currentPage,
                pageSize = collection.perPage,
                start = collection.start,
                count = collection.size(),
                total = collection.totalCount,
                fmts = gettext('<p>Showing <span class="count-current-shown">%(start)s-%(end)s</span> out of <span class="count-total">%(total)s total</span>, sorted by <span class="sort-order">%(sort_order)s</span></p>');

            return interpolate(fmts, {
                    start: start + 1,
                    end: start + count,
                    total: total,
                    sort_order: gettext('Date Added')
                }, true);
        }
    });

    return PagingHeader;
}); // end define();
