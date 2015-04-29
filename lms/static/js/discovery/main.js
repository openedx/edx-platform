RequireJS.require([
    'jquery',
    'backbone',
    'js/discovery/app',
    'js/discovery/collection',
    'js/discovery/form',
    'js/discovery/result_list_view',
    'js/discovery/filter_bar_view',
    'js/discovery/search_facets_view'
], function ($, Backbone, App, Collection, DiscoveryForm, ResultListView, FilterBarView, FacetsBarView) {
    'use strict';

    var app = new App(
        Collection,
        DiscoveryForm,
        ResultListView,
        FilterBarView,
        FacetsBarView,
        getParameterByName('search_query')
    );

});
