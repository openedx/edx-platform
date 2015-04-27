RequireJS.require([
    'jquery',
    'backbone',
    'js/discovery/app',
    'js/discovery/collection',
    'js/discovery/form',
    'js/discovery/result_list_view'
], function ($, Backbone, App, Collection, DiscoveryForm, ResultListView) {
    'use strict';

    var app = new App(
        Collection,
        DiscoveryForm,
        ResultListView,
        getParameterByName('search_query')
    );

});
