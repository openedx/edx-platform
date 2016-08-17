;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'text!common/templates/components/paging-header.underscore'
    ], function (Backbone, _, gettext, headerTemplate) {
        var PagingHeader = Backbone.View.extend({
            initialize: function (options) {
                this.srInfo = options.srInfo;
                this.showSortControls = options.showSortControls;
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            events: {
                'change #paging-header-select': 'sortCollection'
            },

            render: function () {
                var message,
                    start = _.isUndefined(this.collection.start) ? 0 : this.collection.start,
                    end = start + this.collection.length,
                    num_items = _.isUndefined(this.collection.totalCount) ? 0 : this.collection.totalCount,
                    context = {first_index: Math.min(start + 1, end), last_index: end, num_items: num_items};
                if (end <= 1) {
                    message = interpolate(gettext('Showing %(first_index)s out of %(num_items)s total'), context, true);
                } else {
                    message = interpolate(
                        gettext('Showing %(first_index)s-%(last_index)s out of %(num_items)s total'),
                        context, true
                    );
                }
                this.$el.html(_.template(headerTemplate, {
                    message: message,
                    srInfo: this.srInfo,
                    sortableFields: this.collection.sortableFields,
                    sortOrder: this.sortOrder,
                    showSortControls: this.showSortControls
                }));
                return this;
            },

            /**
             * Updates the collection's sort order, and fetches an updated set of
             * results.
             * @returns {*} A promise for the collection being updated
             */
            sortCollection: function () {
                var selected = this.$('#paging-header-select option:selected');
                this.sortOrder = selected.attr('value');
                this.collection.setSortField(this.sortOrder);
                return this.collection.refresh();
            }
        });
        return PagingHeader;
    });
}).call(this, define || RequireJS.define);
