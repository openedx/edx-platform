/* globals loadFixtures, Logger */

'use strict';

import 'jquery';
import Backbone from 'backbone';

import AjaxHelpers from 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers';
import CourseSearchFactory from 'course_search/js/course_search_factory';
import CourseSearchResultsView from 'course_search/js/views/course_search_results_view';
import DashboardSearchFactory from 'course_search/js/dashboard_search_factory';
import DashboardSearchResultsView from 'course_search/js/views/dashboard_search_results_view';
import PageHelpers from 'common/js/spec_helpers/page_helpers';
import SearchCollection from 'course_search/js/collections/search_collection';
import SearchForm from 'course_search/js/views/search_form';
import SearchItemView from 'course_search/js/views/search_item_view';
import SearchResult from 'course_search/js/models/search_result';
import SearchRouter from 'course_search/js/search_router';

import courseSearchItemTemplate from 'text!course_search/templates/course_search_item.underscore';

describe('Course Search', () => {
  beforeEach(() => {
    PageHelpers.preventBackboneChangingUrl();
  });


  describe('SearchResult', () => {
    beforeEach(function before() {
      this.result = new SearchResult();
    });

    it('has properties', function test() {
      expect(this.result.get('location')).toBeDefined();
      expect(this.result.get('content_type')).toBeDefined();
      expect(this.result.get('excerpt')).toBeDefined();
      expect(this.result.get('url')).toBeDefined();
    });
  });


  describe('SearchCollection', () => {
    beforeEach(function before() {
      this.collection = new SearchCollection();

      this.onSearch = jasmine.createSpy('onSearch');
      this.collection.on('search', this.onSearch);

      this.onNext = jasmine.createSpy('onNext');
      this.collection.on('next', this.onNext);

      this.onError = jasmine.createSpy('onError');
      this.collection.on('error', this.onError);
    });

    it('sends a request without a course ID', () => {
      const collection = new SearchCollection([]);
      spyOn($, 'ajax');
      collection.performSearch('search string');
      expect($.ajax.calls.mostRecent().args[0].url).toEqual('/search/');
    });

    it('sends a request with course ID', () => {
      const collection = new SearchCollection([], { courseId: 'edx101' });
      spyOn($, 'ajax');
      collection.performSearch('search string');
      expect($.ajax.calls.mostRecent().args[0].url).toEqual('/search/edx101');
    });

    it('sends a request and parses the json result', function test() {
      const requests = AjaxHelpers.requests(this);
      const response = {
        total: 2,
        access_denied_count: 1,
        results: [{
          data: {
            location: ['section', 'subsection', 'unit'],
            url: '/some/url/to/content',
            content_type: 'text',
            excerpt: 'this is a short excerpt',
          },
        }],
      };
      this.collection.performSearch('search string');
      AjaxHelpers.respondWithJson(requests, response);

      expect(this.onSearch).toHaveBeenCalled();
      expect(this.collection.totalCount).toEqual(1);
      expect(this.collection.latestModelsCount).toEqual(1);
      expect(this.collection.accessDeniedCount).toEqual(1);
      expect(this.collection.page).toEqual(0);
      expect(this.collection.first().attributes).toEqual(response.results[0].data);
    });

    it('handles errors', function test() {
      const requests = AjaxHelpers.requests(this);
      this.collection.performSearch('search string');
      AjaxHelpers.respondWithError(requests, 500);
      expect(this.onSearch).not.toHaveBeenCalled();
      expect(this.onError).toHaveBeenCalled();
    });

    it('loads next page', function test() {
      const requests = AjaxHelpers.requests(this);
      const response = { total: 35, results: [] };
      this.collection.loadNextPage();
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.onNext).toHaveBeenCalled();
      expect(this.onError).not.toHaveBeenCalled();
    });

    it('sends correct paging parameters', function test() {
      const requests = AjaxHelpers.requests(this);
      const searchString = 'search string';
      const response = { total: 52, results: [] };
      this.collection.performSearch(searchString);
      AjaxHelpers.respondWithJson(requests, response);
      this.collection.loadNextPage();
      AjaxHelpers.respondWithJson(requests, response);
      spyOn($, 'ajax');
      this.collection.loadNextPage();
      expect($.ajax.calls.mostRecent().args[0].url).toEqual(this.collection.url);
      expect($.ajax.calls.mostRecent().args[0].data.search_string).toEqual(searchString);
      expect($.ajax.calls.mostRecent().args[0].data.page_size).toEqual(this.collection.pageSize);
      expect($.ajax.calls.mostRecent().args[0].data.page_index).toEqual(2);
    });

    it('has next page', function test() {
      const requests = AjaxHelpers.requests(this);
      const response = { total: 35, access_denied_count: 5, results: [] };
      this.collection.performSearch('search string');
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.collection.hasNextPage()).toEqual(true);
      this.collection.loadNextPage();
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.collection.hasNextPage()).toEqual(false);
    });

    it('aborts any previous request', function test() {
      const requests = AjaxHelpers.requests(this);
      const response = { total: 35, results: [] };

      this.collection.performSearch('old search');
      this.collection.performSearch('new search');
      AjaxHelpers.skipResetRequest(requests);
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.onSearch.calls.count()).toEqual(1);

      this.collection.performSearch('old search');
      this.collection.cancelSearch();
      AjaxHelpers.skipResetRequest(requests);
      expect(this.onSearch.calls.count()).toEqual(1);

      this.collection.loadNextPage();
      this.collection.loadNextPage();
      AjaxHelpers.skipResetRequest(requests);
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.onNext.calls.count()).toEqual(1);
    });

    describe('reset state', () => {
      beforeEach(function before() {
        this.collection.page = 2;
        this.collection.totalCount = 35;
        this.collection.latestModelsCount = 5;
      });

      it('resets state when performing new search', function test() {
        this.collection.performSearch('search string');
        expect(this.collection.models.length).toEqual(0);
        expect(this.collection.page).toEqual(0);
        expect(this.collection.totalCount).toEqual(0);
        expect(this.collection.latestModelsCount).toEqual(0);
      });

      it('resets state when canceling a search', function test() {
        this.collection.cancelSearch();
        expect(this.collection.models.length).toEqual(0);
        expect(this.collection.page).toEqual(0);
        expect(this.collection.totalCount).toEqual(0);
        expect(this.collection.latestModelsCount).toEqual(0);
      });
    });
  });


  describe('SearchRouter', () => {
    beforeEach(function before() {
      this.router = new SearchRouter();
      this.onSearch = jasmine.createSpy('onSearch');
      this.router.on('search', this.onSearch);
    });

    it('has a search route', function test() {
      expect(this.router.routes['search/:query']).toEqual('search');
    });

    it('triggers a search event', function test() {
      const query = 'mercury';
      this.router.search(query);
      expect(this.onSearch).toHaveBeenCalledWith(query);
    });
  });

  describe('SearchItemView', () => {
    beforeEach(function before() {
      this.model = new SearchResult({
        location: ['section', 'subsection', 'unit'],
        content_type: 'Video',
        course_name: 'Course Name',
        excerpt: 'A short excerpt.',
        url: 'path/to/content',
      });

      this.seqModel = new SearchResult({
        location: ['section', 'subsection'],
        content_type: 'Sequence',
        course_name: 'Course Name',
        excerpt: 'A short excerpt.',
        url: 'path/to/content',
      });

      this.item = new SearchItemView({
        model: this.model,
        template: courseSearchItemTemplate,
      });
      this.item.render();
      this.seqItem = new SearchItemView({
        model: this.seqModel,
        template: courseSearchItemTemplate,
      });
      this.seqItem.render();
    });

    it('rendersItem', function test() {
      expect(this.item.$el).toHaveAttr('role', 'region');
      expect(this.item.$el).toHaveAttr('aria-label', 'search result');
      expect(this.item.$el).toContainElement(`a[href="${this.model.get('url')}"]`);
      expect(this.item.$el.find('.result-type')).toContainHtml(this.model.get('content_type'));
      expect(this.item.$el.find('.result-excerpt')).toContainHtml(this.model.get('excerpt'));
      expect(this.item.$el.find('.result-location')).toContainHtml('section ▸ subsection ▸ unit');
    });

    it('rendersSequentialItem', function test() {
      expect(this.seqItem.$el).toHaveAttr('role', 'region');
      expect(this.seqItem.$el).toHaveAttr('aria-label', 'search result');
      expect(this.seqItem.$el).toContainElement(`a[href="${this.seqModel.get('url')}"]`);
      expect(this.seqItem.$el.find('.result-type')).toBeEmpty();
      expect(this.seqItem.$el.find('.result-excerpt')).toBeEmpty();
      expect(this.seqItem.$el.find('.result-location')).toContainHtml('section ▸ subsection');
    });

    it('logsSearchItemViewEvent', function test() {
      this.model.collection = new SearchCollection([this.model], { course_id: 'edx101' });
      this.item.render();
      // Mock the redirect call
      spyOn(SearchItemView, 'redirect').and.callFake(() => {});
      spyOn(Logger, 'log').and.returnValue($.Deferred().resolve());
      this.item.$el.find('a').trigger('click');
      expect(SearchItemView.redirect).toHaveBeenCalled();
      this.item.$el.trigger('click');
      expect(SearchItemView.redirect).toHaveBeenCalled();
    });
  });


  describe('SearchForm', () => {
    function trimsInputString() {
      const term = '    search string  ';
      $('.search-field').val(term);
      $('form').trigger('submit');
      expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
    }

    function doesSearch() {
      const term = '  search string  ';
      $('.search-field').val(term);
      this.form.doSearch(term);
      expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
      expect($('.search-field').val()).toEqual(term.trim());
      expect($('.search-field')).toHaveClass('is-active');
      expect($('.search-button')).toBeHidden();
      expect($('.cancel-button')).toBeVisible();
    }

    function triggersSearchEvent() {
      const term = 'search string';
      $('.search-field').val(term);
      $('form').trigger('submit');
      expect(this.onSearch).toHaveBeenCalledWith(term);
      expect($('.search-field')).toHaveClass('is-active');
      expect($('.search-button')).toBeHidden();
      expect($('.cancel-button')).toBeVisible();
    }

    function clearsSearchOnCancel() {
      $('.search-field').val('search string');
      $('.search-button').trigger('click');
      $('.cancel-button').trigger('click');
      expect($('.search-field')).not.toHaveClass('is-active');
      expect($('.search-button')).toBeVisible();
      expect($('.cancel-button')).toBeHidden();
      expect($('.search-field')).toHaveValue('');
    }

    function clearsSearchOnEmpty() {
      $('.search-field').val('');
      $('form').trigger('submit');
      expect(this.onClear).toHaveBeenCalled();
      expect($('.search-field')).not.toHaveClass('is-active');
      expect($('.cancel-button')).toBeHidden();
      expect($('.search-button')).toBeVisible();
    }

    describe('SearchForm', () => {
      beforeEach(function before() {
        loadFixtures('course_search/fixtures/course_content_page.html');
        this.form = new SearchForm({
          el: '.search-bar',
        });
        this.onClear = jasmine.createSpy('onClear');
        this.onSearch = jasmine.createSpy('onSearch');
        this.form.on('clear', this.onClear);
        this.form.on('search', this.onSearch);
      });
      it('trims input string', trimsInputString);
      it('handles calls to doSearch', doesSearch);
      it('triggers a search event and changes to active state', triggersSearchEvent);
      it('clears search when clicking on cancel button', clearsSearchOnCancel);
      it('clears search when search box is empty', clearsSearchOnEmpty);
    });
  });


  describe('SearchResultsView', () => {
    function showsLoadingMessage() {
      this.resultsView.showLoadingMessage();
      expect(this.resultsView.$el).toBeVisible();
      expect(this.resultsView.$el).not.toBeEmpty();
    }

    function showsErrorMessage() {
      this.resultsView.showErrorMessage();
      expect(this.resultsView.$el).toBeVisible();
      expect(this.resultsView.$el).not.toBeEmpty();
    }

    function returnsToContent() {
      this.resultsView.clear();
      expect(this.resultsView.$el).toBeHidden();
      expect(this.resultsView.$el).toBeEmpty();
    }

    function showsNoResultsMessage() {
      this.collection.reset();
      this.resultsView.render();
      expect(this.resultsView.$el).toContainHtml('no results');
      expect(this.resultsView.$el.find('ol')).not.toExist();
    }

    function rendersSearchResults() {
      const searchResults = [{
        location: ['section', 'subsection', 'unit'],
        url: '/some/url/to/content',
        content_type: 'text',
        course_name: '',
        excerpt: 'this is a short excerpt',
      }];
      this.collection.set(searchResults);
      this.collection.latestModelsCount = 1;
      this.collection.totalCount = 1;

      this.resultsView.render();
      expect(this.resultsView.$el.find('ol')[0]).toExist();
      expect(this.resultsView.$el.find('li').length).toEqual(1);
      expect(this.resultsView.$el).toContainHtml('Search Results');
      expect(this.resultsView.$el).toContainHtml('this is a short excerpt');

      this.collection.set(searchResults);
      this.collection.totalCount = 2;
      this.resultsView.renderNext();
      expect(this.resultsView.$el.find('.search-count')).toContainHtml('2');
      expect(this.resultsView.$el.find('li').length).toEqual(2);
    }

    function showsMoreResultsLink() {
      this.collection.totalCount = 123;
      this.collection.hasNextPage = () => true;
      this.resultsView.render();
      expect(this.resultsView.$el.find('a.search-load-next')[0]).toExist();

      this.collection.totalCount = 123;
      this.collection.hasNextPage = () => false;
      this.resultsView.render();
      expect(this.resultsView.$el.find('a.search-load-next')[0]).not.toExist();
    }

    function triggersNextPageEvent() {
      const onNext = jasmine.createSpy('onNext');
      this.resultsView.on('next', onNext);
      this.collection.totalCount = 123;
      this.collection.hasNextPage = () => true;
      this.resultsView.render();
      this.resultsView.$el.find('a.search-load-next').click();
      expect(onNext).toHaveBeenCalled();
    }

    function showsLoadMoreSpinner() {
      this.collection.totalCount = 123;
      this.collection.hasNextPage = () => true;
      this.resultsView.render();
      expect(this.resultsView.$el.find('a.search-load-next .icon')).toBeHidden();
      this.resultsView.loadNext();
          // toBeVisible does not work with inline
      expect(this.resultsView.$el.find('a.search-load-next .icon')).toHaveCss({
        display: 'inline',
      });
      this.resultsView.renderNext();
      expect(this.resultsView.$el.find('a.search-load-next .icon')).toBeHidden();
    }

    function beforeEachHelper(SearchResultsView) {
      const MockCollection = Backbone.Collection.extend({
        hasNextPage() {},
        latestModelsCount: 0,
        pageSize: 20,
        latestModels(...args) {
          return SearchCollection.prototype.latestModels.apply(this, ...args);
        },
      });

      this.collection = new MockCollection();
      this.resultsView = new SearchResultsView({ collection: this.collection });
    }

    describe('CourseSearchResultsView', () => {
      beforeEach(function before() {
        loadFixtures('course_search/fixtures/course_content_page.html');
        beforeEachHelper.call(this, CourseSearchResultsView);
        this.contentElementDisplayValue = 'table-cell';
      });
      it('shows loading message', showsLoadingMessage);
      it('shows error message', showsErrorMessage);
      xit('returns to content', returnsToContent);
      it('shows a message when there are no results', showsNoResultsMessage);
      it('renders search results', rendersSearchResults);
      it('shows a link to load more results', showsMoreResultsLink);
      it('triggers an event for next page', triggersNextPageEvent);
      it('shows a spinner when loading more results', showsLoadMoreSpinner);
    });

    describe('DashboardSearchResultsView', () => {
      beforeEach(function before() {
        loadFixtures('course_search/fixtures/dashboard_search_page.html');
        beforeEachHelper.call(this, DashboardSearchResultsView);
        this.contentElementDisplayValue = 'block';
      });
      it('shows loading message', showsLoadingMessage);
      it('shows error message', showsErrorMessage);
      it('returns to content', returnsToContent);
      it('shows a message when there are no results', showsNoResultsMessage);
      it('renders search results', rendersSearchResults);
      it('shows a link to load more results', showsMoreResultsLink);
      it('triggers an event for next page', triggersNextPageEvent);
      it('shows a spinner when loading more results', showsLoadMoreSpinner);
    });
  });


  describe('SearchApp', () => {
    function showsLoadingMessage() {
      $('.search-field').val('search string');
      $('.search-button').trigger('click');
      expect(this.$searchResults).toBeVisible();
      expect(this.$searchResults).not.toBeEmpty();
    }

    function performsSearch() {
      const requests = AjaxHelpers.requests(this);
      $('.search-field').val('search string');
      $('.search-button').trigger('click');
      AjaxHelpers.respondWithJson(requests, {
        total: 1337,
        access_denied_count: 12,
        results: [{
          data: {
            location: ['section', 'subsection', 'unit'],
            url: '/some/url/to/content',
            content_type: 'text',
            excerpt: 'this is a short excerpt',
            course_name: '',
          },
        }],
      });
      expect($('.search-info')).toExist();
      expect($('.search-result-list')).toBeVisible();
      expect(this.$searchResults.find('li').length).toEqual(1);
    }

    function showsErrorMessage() {
      const requests = AjaxHelpers.requests(this);
      $('.search-field').val('search string');
      $('.search-button').trigger('click');
      AjaxHelpers.respondWithError(requests, 500, {});
      expect(this.$searchResults).toContainHtml('There was an error');
    }

    function updatesNavigationHistory() {
      $('.search-field').val('edx');
      $('.search-button').trigger('click');
      expect(Backbone.history.navigate.calls.mostRecent().args[0]).toContain('search/edx');
      $('.cancel-button').trigger('click');
      expect(Backbone.history.navigate.calls.argsFor(1)[0]).toBe('');
    }

    function cancelsSearchRequest() {
      const requests = AjaxHelpers.requests(this);
      // send search request to server
      $('.search-field').val('search string');
      $('.search-button').trigger('click');
      // cancel the search and then skip the request that was marked as reset
      $('.cancel-button').trigger('click');
      AjaxHelpers.skipResetRequest(requests);
      // there should be no results
      expect(this.$searchResults).toBeHidden();
    }

    function clearsResults() {
      $('.cancel-button').trigger('click');
      expect(this.$searchResults).toBeHidden();
    }

    function loadsNextPage() {
      const requests = AjaxHelpers.requests(this);
      const response = {
        total: 1337,
        access_denied_count: 12,
        results: [{
          data: {
            location: ['section', 'subsection', 'unit'],
            url: '/some/url/to/content',
            content_type: 'text',
            excerpt: 'this is a short excerpt',
            course_name: '',
          },
        }],
      };
      $('.search-field').val('query');
      $('.search-button').trigger('click');
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.$searchResults.find('li').length).toEqual(1);
      expect($('.search-load-next')).toBeVisible();
      $('.search-load-next').trigger('click');
      const body = requests[1].requestBody;
      expect(body).toContain('search_string=query');
      expect(body).toContain('page_index=1');
      AjaxHelpers.respondWithJson(requests, response);
      expect(this.$searchResults.find('li').length).toEqual(2);
    }

    function navigatesToSearch() {
      const requests = AjaxHelpers.requests(this);
      Backbone.history.start();
      Backbone.history.loadUrl('search/query');
      expect(requests[0].requestBody).toContain('search_string=query');
    }

    describe('CourseSearchApp', () => {
      beforeEach(function before() {
        const courseId = 'a/b/c';
        loadFixtures('course_search/fixtures/course_content_page.html');
        this.factory = new CourseSearchFactory({
          courseId,
          searchHeader: $('.search-bar'),
        });
        spyOn(Backbone.history, 'navigate');
        this.$contentElement = $('#course-content');
        this.contentElementDisplayValue = 'table-cell';
        this.$searchResults = $('.search-results');
      });

      afterEach(() => {
        Backbone.history.stop();
      });

      it('shows loading message on search', showsLoadingMessage);
      it('performs search', performsSearch);
      it('shows an error message', showsErrorMessage);
      it('updates navigation history', updatesNavigationHistory);
      xit('cancels search request', cancelsSearchRequest);
      xit('clears results', clearsResults);
      it('loads next page', loadsNextPage);
      it('navigates to search', navigatesToSearch);
    });

    describe('DashboardSearchApp', () => {
      beforeEach(function before() {
        loadFixtures('course_search/fixtures/dashboard_search_page.html');
        this.factory = new DashboardSearchFactory();

        spyOn(Backbone.history, 'navigate');
        this.contentElementDisplayValue = 'block';
        this.$searchResults = $('.search-results');
      });

      afterEach(() => {
        Backbone.history.stop();
      });

      it('shows loading message on search', showsLoadingMessage);
      it('performs search', performsSearch);
      it('shows an error message', showsErrorMessage);
      it('updates navigation history', updatesNavigationHistory);
      it('cancels search request', cancelsSearchRequest);
      it('clears results', clearsResults);
      it('loads next page', loadsNextPage);
      it('navigates to search', navigatesToSearch);
      it('returns to course list', function test() {
        const requests = AjaxHelpers.requests(this);
        $('.search-field').val('search string');
        $('.search-button').trigger('click');
        AjaxHelpers.respondWithJson(requests, {
          total: 1337,
          access_denied_count: 12,
          results: [{
            data: {
              location: ['section', 'subsection', 'unit'],
              url: '/some/url/to/content',
              content_type: 'text',
              excerpt: 'this is a short excerpt',
              course_name: '',
            },
          }],
        });
        $('.search-form .cancel-button').trigger('click');
        expect(this.$searchResults).toBeHidden();
        expect(this.$searchResults).toBeEmpty();
      });
    });

    describe('Course Search Results Page', () => {
      beforeEach(function before() {
        const courseId = 'a/b/c';
        loadFixtures('course_search/fixtures/course_search_results_page.html');
        this.factory = new CourseSearchFactory({
          courseId,
          searchHeader: $('.page-header-search'),
        });
        spyOn(Backbone.history, 'navigate');
        // The search results page does not show over a content element
        this.$contentElement = null;
        this.contentElementDisplayValue = 'table-cell';
        this.$searchResults = $('.search-results');
      });

      afterEach(() => {
        Backbone.history.stop();
      });

      it('shows loading message on search', showsLoadingMessage);
      it('performs search', performsSearch);
      it('shows an error message', showsErrorMessage);
      it('loads next page', loadsNextPage);
    });
  });
});
