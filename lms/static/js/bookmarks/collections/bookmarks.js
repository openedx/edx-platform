;(function (define) {

    define(['backbone', 'js/bookmarks/models/bookmark'],
        function (Backbone, BookmarkModel) {
        'use strict';

        return Backbone.Collection.extend({
            model: BookmarkModel,

            url: function() {
                return $(".courseware-bookmarks-button").data('bookmarksApiUrl');
            },

            parse: function(response) {
                return response.results;
            }
        });
    });

})(define || RequireJS.define);
