(function(define) {
    'use strict';
    define([
        'backbone',
        'edx-ui-toolkit/js/pagination/paging-collection',
        'js/bookmarks/models/bookmark'
    ], function(Backbone, PagingCollection, BookmarkModel) {
        return PagingCollection.extend({
            model: BookmarkModel,

            queryParams: {
                course_id: function() { return this.options.course_id; },
                fields: function() { return 'display_name,path'; }
            },

            url: function() {
                return this.url;
            },

            constructor: function(models, options) {
                this.options = options;
                this.url = options.url;
                PagingCollection.prototype.constructor.call(this, models, options);
            }
        });
    });
})(define || RequireJS.define);

