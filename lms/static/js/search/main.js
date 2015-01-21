RequireJS.require([
    'jquery',
    'backbone',
    'js/search/SearchApp'
], function ($, Backbone, SearchApp) {
    'use strict';

    var course_id = $('#courseware-search-results').attr('data-course-id');
    var app = new SearchApp(course_id);
    Backbone.history.start();

});
