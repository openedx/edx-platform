;(function (define) {

define([
    'js/search/base/views/search_item_view'
], function (SearchItemView) {
    'use strict';

    return SearchItemView.extend({
        templateId: '#dashboard_search_item-tpl'
    });

});

})(define || RequireJS.define);
