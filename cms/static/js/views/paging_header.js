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
            this.render();
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
                fmts = gettext('Showing %(current_span)s%(start)s-%(end)s%(end_span)s out of %(total_span)s%(total)s total%(end_span)s, sorted by %(order_span)s%(sort_order)s%(end_span)s');

            return '<p>' + interpolate(fmts, {
                    start: start + 1,
                    end: start + count,
                    total: total,
                    sort_order: gettext('Date Added'),
                    current_span: '<span class="count-current-shown">',
                    total_span: '<span class="count-total">',
                    order_span: '<span class="sort-order">',
                    end_span: '</span>'
                }, true) + "</p>";
        }
    });

    return PagingHeader;
}); // end define();
