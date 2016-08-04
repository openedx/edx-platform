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
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'common/js/components/views/list',
        'text!common/templates/components/paginated-view.underscore'
    ], function (Backbone, _, HtmlUtils, PagingHeader, PagingFooter, ListView, paginatedViewTemplate) {
        var PaginatedView = Backbone.View.extend({
            initialize: function () {
                var ItemListView = this.listViewClass.extend({
                    tagName: 'div',
                    className: this.type  + '-container',
                    itemViewClass: this.itemViewClass
                });
                this.listView = new ItemListView({collection: this.collection});
                this.headerView = this.createHeaderView();
                this.footerView = this.createFooterView();
                this.collection.on('page_changed', function () {
                    this.$('.sr-is-focusable.sr-' + this.type + '-view').focus();
                }, this);
            },

            listViewClass: ListView,

            viewTemplate: paginatedViewTemplate,

            paginationLabel: gettext("Pagination"),

            createHeaderView: function() {
                return new PagingHeader({collection: this.collection, srInfo: this.srInfo});
            },

            createFooterView: function() {
                return new PagingFooter({
                    collection: this.collection,
                    hideWhenOnePage: true,
                    paginationLabel: this.paginationLabel
                });
            },

            render: function () {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.viewTemplate)({type: this.type}));
                this.assign(this.listView, '.' + this.type + '-list');
                if (this.headerView) {
                    this.assign(this.headerView, '.' + this.type + '-paging-header');
                }
                if (this.footerView) {
                    this.assign(this.footerView, '.' + this.type + '-paging-footer');
                }
                return this;
            },

            renderError: function () {
                this.$el.text(
                    gettext('Your request could not be completed. Reload the page and try again. If the issue persists, click the Help tab to report the problem.')  // eslint-disable-line max-len
                );
            },

            assign: function (view, selector) {
                view.setElement(this.$(selector)).render();
            }
        });

        return PaginatedView;
    });
}).call(this, define || RequireJS.define);
