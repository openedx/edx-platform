define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'js/models/asset'
], function(_, PagingCollection, AssetModel) {
    'use strict';

    var AssetCollection = PagingCollection.extend({
        assetType: '',
        model: AssetModel,

        state: {
            firstPage: 0,
            pageSize: 50,
            sortKey: 'sort',
            order: null,
            currentPage: null,
            totalRecords: null,
            totalCount: null
        },

        queryParams: {
            currentPage: 'page',
            pageSize: 'page_size',
            sortKey: 'sort',
            order: 'direction',
            directions: {
                asc: 'asc',
                desc: 'desc'
            },
            asset_type: function() { return this.assetType; }
        },

        parse: function(response, options) {
            response.results = response.assets;
            delete response.assets;
            return PagingCollection.prototype.parse.call(this, response, options);
        },

        parseState: function(response) {
            return {
                totalRecords: response[0].totalCount,
                totalPages: Math.ceil(response[0].totalCount / response[0].pageSize)
            };
        }
    });

    return AssetCollection;
});
