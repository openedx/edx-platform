define(["underscore", "gettext", "js/views/baseview"], function(_, gettext, BaseView) {

    var PagingHeader = BaseView.extend({
        events : {
            "click .next-page-link": "nextPage",
            "click .previous-page-link": "previousPage"
        },

        initialize: function(options) {
            var view = options.view,
                collection = view.collection;
            this.view = view;
            this.template = this.loadTemplate('paging-header');
            collection.bind('add', _.bind(this.render, this));
            collection.bind('remove', _.bind(this.render, this));
            collection.bind('reset', _.bind(this.render, this));
        },

        render: function() {
            var view = this.view,
                collection = view.collection,
                currentPage = collection.currentPage,
                lastPage = collection.totalPages - 1,
                messageHtml = this.messageHtml();
            this.$el.html(this.template({
                messageHtml: messageHtml
            }));
            this.$(".previous-page-link").toggleClass("is-disabled", currentPage === 0);
            this.$(".next-page-link").toggleClass("is-disabled", currentPage === lastPage);
            return this;
        },

        messageHtml: function() {
            var view = this.view,
                collection = view.collection,
                start = collection.start,
                count = collection.size(),
                sortName = view.sortDisplayName(),
                sortDirectionName = view.sortDirectionName(),
                end = start + count,
                total = collection.totalCount,
                fmts = gettext('Showing %(current_span)s%(start)s-%(end)s%(end_span)s out of %(total_span)s%(total)s total%(end_span)s, sorted by %(order_span)s%(sort_order)s%(end_span)s %(sort_direction)s');

            return '<p>' + interpolate(fmts, {
                start: Math.min(start + 1, end),
                end: end,
                total: total,
                sort_order: sortName,
                sort_direction: sortDirectionName,
                current_span: '<span class="count-current-shown">',
                total_span: '<span class="count-total">',
                order_span: '<span class="sort-order">',
                end_span: '</span>'
            }, true) + "</p>";
        },

        nextPage: function() {
            this.view.nextPage();
        },

        previousPage: function() {
            this.view.previousPage();
        }
    });

    return PagingHeader;
}); // end define();
