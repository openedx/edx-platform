'use strict';

import _ from 'underscore';
import Backbone from 'backbone';

import DashboardSearchResultsView from './views/dashboard_search_results_view';
import SearchCollection from './collections/search_collection';
import SearchForm from './views/search_form';
import SearchRouter from './search_router';

class DashboardSearchFactory {
  constructor() {
    const router = new SearchRouter();
    const form = new SearchForm({
      el: $('#dashboard-search-bar'),
    });
    const collection = new SearchCollection([]);
    const results = new DashboardSearchResultsView({ collection });
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

    dispatcher.listenTo(results, 'reset', () => {
      form.resetSearchForm();
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
  }
}
export { DashboardSearchFactory as default };
