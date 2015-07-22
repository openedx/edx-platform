;(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'common/js/components/views/list',
        'text!common/templates/components/paginated-view.underscore'
    ], function (Backbone, _, PagingHeader, PagingFooter, ListView, paginatedViewTemplate) {
        var PaginatedView = Backbone.View.extend({
            initialize: function () {
                var ItemListView = ListView.extend({
                    tagName: 'div',
                    className: this.type  + '-container',
                    itemViewClass: this.itemViewClass
                });
                this.listView = new ItemListView({collection: this.options.collection});
                this.headerView = this.headerView = new PagingHeader({collection: this.options.collection});
                this.footerView = new PagingFooter({
                    collection: this.options.collection, hideWhenOnePage: true
                });
                this.collection.on('page_changed', function () {
                    this.$('.sr-is-focusable.sr-' + this.type + '-view').focus();
                }, this);
            },

            render: function () {
                this.$el.html(_.template(paginatedViewTemplate, {type: this.type}));
                this.assign(this.listView, '.' + this.type + '-list');
                this.assign(this.headerView, '.' + this.type + '-paging-header');
                this.assign(this.footerView, '.' + this.type + '-paging-footer');
                return this;
            },

            assign: function (view, selector) {
                view.setElement(this.$(selector)).render();
            }
        });

        return PaginatedView;
    });
}).call(this, define || RequireJS.define);
