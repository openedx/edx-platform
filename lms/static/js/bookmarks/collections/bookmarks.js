;(function (define) {
    'use strict';
    define(['backbone', 'common/js/components/collections/paging_collection', 'js/bookmarks/models/bookmark'],
        function (Backbone, PagingCollection, BookmarkModel) {

            return PagingCollection.extend({
                initialize: function(options) {
                    PagingCollection.prototype.initialize.call(this);

                    this.url = options.url;
                    this.server_api.course_id = function () { return encodeURIComponent(options.course_id); };
                    this.server_api.fields = function () { return encodeURIComponent('display_name,path'); };
                    delete this.server_api.sort_order; // Sort order is not specified for the Bookmark API
                },

                model: BookmarkModel,

                url: function() {
                    return this.url;
                }
            });
    });

})(define || RequireJS.define);