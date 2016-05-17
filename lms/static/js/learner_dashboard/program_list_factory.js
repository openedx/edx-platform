;(function (define) {
    'use strict';

    define([
        'js/learner_dashboard/views/collection_list_view',
        'js/learner_dashboard/views/sidebar_view',
        'js/learner_dashboard/views/program_card_view',
        'js/learner_dashboard/collections/program_collection'
    ],
    function (CollectionListView, SidebarView, ProgramCardView, ProgramCollection) {
        return function (options) {
            new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                context: options,
                collection: new ProgramCollection(options.programsData)
            }).render();

            new SidebarView({
                el: '.sidebar',
                context: options
            }).render();
        };
    });
}).call(this, define || RequireJS.define);
