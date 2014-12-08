RequireJS.define([
    'backbone',
    'js/search/SearchRouter',
    'js/search/views/SearchForm',
    'js/search/views/SearchListView',
    'js/search/collections/SearchCollection'
], function(Backbone, SearchRouter, SearchForm, SearchListView, SearchCollection) {
    'use strict';

    return function (course_id) {

        var self = this;

        this.router = new SearchRouter();
        this.form = new SearchForm();
        this.collection = new SearchCollection([], { course_id: course_id });
        this.results = new SearchListView({ collection: this.collection });

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

});
