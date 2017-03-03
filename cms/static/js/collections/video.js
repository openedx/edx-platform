define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'js/models/asset'
], function(_, PagingCollection) {
    'use strict';

    var VideoPagingCollection = PagingCollection.extend({

        initialize: function(models, options) {
            this.state = this.initState(options);
            this.url = options.url;
            PagingCollection.prototype.initialize.call(this, models, options);
        },

        queryParams: {
            currentPage: 'page',
            pageSize: 'page_size',
            sortKey: 'sort_field',
            order: 'sort_order',
            directions: {
                asc: 'asc',
                desc: 'desc'
            }
        },

        initState: function(options) {
            return {
                pageSize: options.pageSize,
                totalRecords: options.count,
                sortKey: options.sortField,
                order: options.sort_order
            };
        },

        parseState: function(response) {
            return {
                totalRecords: response[0].count,
                totalPages: response[0].num_pages
            };
        }
    });


    return VideoPagingCollection;
});
