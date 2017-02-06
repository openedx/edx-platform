define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'js/models/asset'
], function(_, PagingCollection) {
    'use strict';

    var VideoPagingCollection = PagingCollection.extend({
        state: {
            firstPage: 0,
            pageSize: 50,
            currentPage: 0,
        },

        queryParams: {
            currentPage: 'page',
            pageSize: 'page_size',
        },
    });

    return VideoPagingCollection;
});
