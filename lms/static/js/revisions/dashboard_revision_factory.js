;(function (define) {
    'use strict';

    define(['backbone', 'js/revisions/collections/revision_collection', 'js/revisions/views/revision_list_view'],
        function(Backbone, RevisionCollection, RevisionListView) {

            return function () {

                var collection = new RevisionCollection([]);
                var view = new RevisionListView({ collection: collection });
                var dispatcher = _.clone(Backbone.Events);

                dispatcher.listenTo(collection, 'revisions_loaded', function() {
                    // The revisions were fetched successfully.
                    view.render();
                });

                dispatcher.listenTo(collection, 'error', function() {
                    // The revisions couldn't be fetched.
                    view.showErrorMessage();
                });

                // Kick off the revision fetch.
                collection.fetchRevisions();

            };

        });

})(define || RequireJS.define);
