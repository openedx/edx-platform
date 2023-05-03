(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils',
        'text!common/templates/components/paging-header.underscore'
    ], function(Backbone, _, gettext, HtmlUtils, StringUtils, headerTemplate) {
        var PagingHeader = Backbone.View.extend({
            initialize: function(options) {
                this.srInfo = options.srInfo;
                this.showSortControls = options.showSortControls;
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            events: {
                'change #paging-header-select': 'sortCollection'
            },

            render: function() {
                var message,
                    start = (this.collection.getPageNumber() - 1) * this.collection.getPageSize(),
                    end = start + this.collection.size(),
                    numItems = this.collection.getTotalRecords(),
                    context = {
                        firstIndex: Math.min(start + 1, end),
                        lastIndex: end,
                        numItems: numItems
                    };

                if (end <= 1) {
                    message = StringUtils.interpolate(
                        gettext('Showing {firstIndex} out of {numItems} total'),
                        context
                    );
                } else {
                    message = StringUtils.interpolate(
                        gettext('Showing {firstIndex}-{lastIndex} out of {numItems} total'),
                        context
                    );
                }

                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.template(headerTemplate)({
                        message: message,
                        srInfo: this.srInfo,
                        sortableFields: this.collection.sortableFields,
                        sortOrder: this.sortOrder,
                        showSortControls: this.showSortControls
                    })
                );
                return this;
            },

            /**
             * Updates the collection's sort order, and fetches an updated set of
             * results.
             * @returns {*} A promise for the collection being updated
             */
            sortCollection: function() {
                var selected = this.$('#paging-header-select option:selected');
                this.sortOrder = selected.attr('value');
                this.collection.setSortField(this.sortOrder);
                return this.collection.refresh();
            }
        });
        return PagingHeader;
    });
}).call(this, define || RequireJS.define);
