'use strict';

import _ from 'underscore';
import Backbone from 'backbone';

import CourseSearchResultsView from 'course_search/js/views/course_search_results_view';
import SearchCollection from 'course_search/js/collections/search_collection';
import SearchForm from 'course_search/js/views/search_form';
import SearchRouter from 'course_search/js/search_router';

class CourseSearchFactory {
  constructor(options) {
    const courseId = options.courseId;
    const requestedQuery = options.query;
    const supportsActive = options.supportsActive;
    const router = new SearchRouter();
    const form = new SearchForm({
      el: options.searchHeader,
      supportsActive,
    });
    const collection = new SearchCollection([], { courseId });
    const results = new CourseSearchResultsView({ collection });
    const dispatcher = _.clone(Backbone.Events);

    dispatcher.listenTo(router, 'search', (query) => {
      form.doSearch(query);
    });

    dispatcher.listenTo(form, 'search', (query) => {
      results.showLoadingMessage();
      collection.performSearch(query);
      router.navigate(`search/${query}`, { replace: true });
    });

    dispatcher.listenTo(form, 'clear', () => {
      collection.cancelSearch();
      results.clear();
      router.navigate('');
    });

    dispatcher.listenTo(results, 'next', () => {
      collection.loadNextPage();
    });

    dispatcher.listenTo(collection, 'search', () => {
      results.render();
    });

    dispatcher.listenTo(collection, 'next', () => {
      results.renderNext();
    });

    dispatcher.listenTo(collection, 'error', () => {
      results.showErrorMessage();
    });

    // Perform a search if an initial query has been provided.
    if (requestedQuery) {
      router.trigger('search', requestedQuery);
    }
  }
}
export { CourseSearchFactory as default };
