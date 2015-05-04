;(function (define) {

    define(['backbone', 'js/bookmarks/models/bookmark'],
        function (Backbone, BookmarkModel) {
        'use strict';

        return Backbone.Collection.extend({
            model : BookmarkModel,

            parse: function(response) {
                return response.results;
            }
        });
    });

})(define || RequireJS.define);