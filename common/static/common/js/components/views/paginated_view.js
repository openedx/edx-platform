/**
 * A base class for a view which renders and paginates a collection,
 * along with a header and footer displaying controls for
 * pagination.
 *
 * Subclasses should define a `type` property which will be used to
 * create class names for the different subcomponents, as well as an
 * `itemViewClass` which will be used to display each individual
 * element of the collection.
 *
 * If provided, the `srInfo` property will be used to provide
 * information for screen readers on each item. The `srInfo.text`
 * property will be shown in the header, and the `srInfo.id` property
 * will be used to connect each card's title with the header text via
 * the ARIA describedby attribute.
 */
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
                this.headerView = this.createHeaderView();
                this.footerView = this.createFooterView();
                this.collection.on('page_changed', function () {
                    this.$('.sr-is-focusable.sr-' + this.type + '-view').focus();
                }, this);
            },

            createHeaderView: function() {
                return new PagingHeader({collection: this.options.collection, srInfo: this.srInfo});
            },

            createFooterView: function() {
                return new PagingFooter({
                    collection: this.options.collection, hideWhenOnePage: true
                });
            },

            render: function () {
                this.$el.html(_.template(paginatedViewTemplate, {type: this.type}));
                this.assign(this.listView, '.' + this.type + '-list');
                if (this.headerView) {
                    this.assign(this.headerView, '.' + this.type + '-paging-header');
                }
                if (this.footerView) {
                    this.assign(this.footerView, '.' + this.type + '-paging-footer');
                }
                return this;
            },

            assign: function (view, selector) {
                view.setElement(this.$(selector)).render();
            }
        });

        return PaginatedView;
    });
}).call(this, define || RequireJS.define);
