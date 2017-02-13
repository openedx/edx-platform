define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'js/models/asset'
], function(_, PagingCollection) {
    'use strict';

    var VideoPagingCollection = PagingCollection.extend({

        constructor: function(models, options){
            this.state = this.initState(options);
            PagingCollection.prototype.constructor.call(this, models, options);
        },

        initialize: function(models, options){
            PagingCollection.prototype.initialize.call(this, models, options);
            this.url = options.url;
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
                firstPage: options.first_page,
                lastPage: options.last_page,
                pageSize: options.page_size,
                totalRecords: options.total_count,
                sortKey: options.sort_field,
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

        parse: function(response, options) {
            response.results = response.videos;
            delete response.videos;
            return PagingCollection.prototype.parse.call(this, response, options);
        },

        parseState: function(response) {
            return {
                totalRecords: response[0].total_count,
                totalPages: response[0].end - response[0].start + 1
            };
        }
    });


    return VideoPagingCollection;
});
