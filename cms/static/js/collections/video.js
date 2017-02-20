define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'js/models/asset'
], function(_, PagingCollection) {
    'use strict';

    var VideoPagingCollection = PagingCollection.extend({

        initialize: function(models, options){
            this.state = this.initState(options);
            this.url = options.url;
            PagingCollection.prototype.initialize.call(this, models, options);
        },

        queryParams: {
            currentPage: 'page',
            pageSize: 'page_size',
            sortKey: 'sort_field',
            order: 'sort_dir',
            directions: {
                asc: 'asc',
                desc: 'desc'
            }
        },

        initState: function(options){
            return {
                pageSize: options.pageSize,
                totalRecords: options.totalCount,
                sortKey: options.sortField,
                order: function(options){
                    if (options.sort_dir === 'asc') {
                        return -1
                    } else if (options.sort_dir === 'desc'){
                        return 1
                    } else {
                        return -1
                    }
                }

            };
        },

        parseState: function(response) {
            return {
                totalRecords: response[0].total_count,
                totalPages: response[0].total_pages
            };
        }
    });


    return VideoPagingCollection;
});
