
var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.search = edx.search || {};

    edx.search.App = function (course_id) {
        var self = this;

        this.router = new edx.search.Router();
        this.form = new edx.search.Form();
        this.collection = new edx.search.Collection([], { course_id: course_id });
        this.results = new edx.search.List({ collection: this.collection });

        this.form.on('search', this.results.showLoadingMessage, this.results);
        this.form.on('search', this.collection.performSearch, this.collection);
        this.form.on('search', function (term) {
            self.router.navigate('search/' + term, { replace: true });
        });
        this.form.on('clear', this.collection.cancelSearch, this.collection);
        this.form.on('clear', this.results.clear, this.results);
        this.form.on('clear', this.router.navigate, this.router);

        this.results.on('next', this.collection.loadNextPage, this.collection);
        this.router.on('route:search', this.form.doSearch, this.form);
    };

    var course_id = $('#search-content').attr('data-course-id');
    var app = new edx.search.App(course_id);
    Backbone.history.start();
    return  app;

})(Backbone);
