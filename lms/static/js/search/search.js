
var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.search = edx.search || {};

    edx.search.App = function (course_id) {

        var self = this;

        self.router = new edx.search.Router();
        self.form = new edx.search.Form();
        self.collection = new edx.search.Collection([], { course_id: course_id });
        self.results = new edx.search.List({ collection: self.collection });

        self.form.on('search', self.results.showLoadingMessage, self.results);
        self.form.on('search', self.collection.performSearch, self.collection);
        self.form.on('search', function (term) {
            self.router.navigate('search/' + term, { replace: true });
        });
        self.form.on('clear', self.collection.cancelSearch, self.collection);
        self.form.on('clear', self.results.clear, self.results);
        self.form.on('clear', self.router.navigate, self.router);

        self.results.on('next', self.collection.loadNextPage, self.collection);

        self.router.on('route:search', self.form.doSearch, self.form);
        Backbone.history.start();

    };

    var course_id = $('#search-content').attr('data-course-id');
    return new edx.search.App(course_id);

})(Backbone);
