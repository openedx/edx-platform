define(['jquery',
        'backbone',
        'underscore',
        'common/js/components/collections/paging_collection',
        'common/js/spec_helpers/ajax_helpers'
    ],
    function ($, Backbone, _, PagingCollection, AjaxHelpers) {
        'use strict';

        describe('PagingCollection', function () {
            var collection = new PagingCollection({
                url: '/test_url'
            });
        });
    }
);