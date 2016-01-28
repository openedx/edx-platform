;(function (define) {
    'use strict';
    define([
            'js/bookmarks/views/bookmarks_list_button'
        ],
        function(BookmarksListButton) {
            return function() {
                return new BookmarksListButton();
            };
        }
    );
}).call(this, define || RequireJS.define);
