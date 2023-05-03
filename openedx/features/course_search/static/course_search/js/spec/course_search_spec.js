define([
    'jquery',
    'backbone',
    'logger',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/page_helpers',
    'common/js/spec_helpers/template_helpers',
    'course_search/js/models/search_result',
    'course_search/js/collections/search_collection',
    'course_search/js/search_router',
    'course_search/js/views/search_form',
    'course_search/js/views/search_item_view',
    'course_search/js/views/course_search_results_view',
    'course_search/js/views/dashboard_search_results_view',
    'course_search/js/course_search_factory',
    'course_search/js/dashboard_search_factory',
    'text!course_search/templates/course_search_item.underscore'
], function(
    $,
    Backbone,
    Logger,
    AjaxHelpers,
    PageHelpers,
    TemplateHelpers,
    SearchResult,
    SearchCollection,
    SearchRouter,
    SearchForm,
    SearchItemView,
    CourseSearchResultsView,
    DashSearchResultsView,
    CourseSearchFactory,
    DashboardSearchFactory,
    courseSearchItemTemplate
) {
    'use strict';

    describe('Course Search', function() {
        beforeEach(function() {
            PageHelpers.preventBackboneChangingUrl();
        });

        describe('SearchResult', function() {
            beforeEach(function() {
                this.result = new SearchResult();
            });

            it('has properties', function() {
                expect(this.result.get('location')).toBeDefined();
                expect(this.result.get('content_type')).toBeDefined();
                expect(this.result.get('excerpt')).toBeDefined();
                expect(this.result.get('url')).toBeDefined();
            });
        });


        describe('SearchCollection', function() {
            beforeEach(function() {
                this.collection = new SearchCollection();

                this.onSearch = jasmine.createSpy('onSearch');
                this.collection.on('search', this.onSearch);

                this.onNext = jasmine.createSpy('onNext');
                this.collection.on('next', this.onNext);

                this.onError = jasmine.createSpy('onError');
                this.collection.on('error', this.onError);
            });

            it('sends a request without a course ID', function() {
                var collection = new SearchCollection([]);
                spyOn($, 'ajax');
                collection.performSearch('search string');
                expect($.ajax.calls.mostRecent().args[0].url).toEqual('/search/');
            });

            it('sends a request with course ID', function() {
                var collection = new SearchCollection([], {courseId: 'edx101'});
                spyOn($, 'ajax');
                collection.performSearch('search string');
                expect($.ajax.calls.mostRecent().args[0].url).toEqual('/search/edx101');
            });

            it('sends a request and parses the json result', function() {
                var requests = AjaxHelpers.requests(this);
                var response = {
                    total: 2,
                    access_denied_count: 1,
                    results: [{
                        data: {
                            location: ['section', 'subsection', 'unit'],
                            url: '/some/url/to/content',
                            content_type: 'text',
                            excerpt: 'this is a short excerpt'
                        }
                    }]
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

            it('handles errors', function() {
                var requests = AjaxHelpers.requests(this);
                this.collection.performSearch('search string');
                AjaxHelpers.respondWithError(requests, 500);
                expect(this.onSearch).not.toHaveBeenCalled();
                expect(this.onError).toHaveBeenCalled();
            });

            it('loads next page', function() {
                var requests = AjaxHelpers.requests(this);
                var response = {total: 35, results: []};
                this.collection.loadNextPage();
                AjaxHelpers.respondWithJson(requests, response);
                expect(this.onNext).toHaveBeenCalled();
                expect(this.onError).not.toHaveBeenCalled();
            });

            it('sends correct paging parameters', function() {
                var requests = AjaxHelpers.requests(this);
                var searchString = 'search string';
                var response = {total: 52, results: []};
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

            it('has next page', function() {
                var requests = AjaxHelpers.requests(this);
                var response = {total: 35, access_denied_count: 5, results: []};
                this.collection.performSearch('search string');
                AjaxHelpers.respondWithJson(requests, response);
                expect(this.collection.hasNextPage()).toEqual(true);
                this.collection.loadNextPage();
                AjaxHelpers.respondWithJson(requests, response);
                expect(this.collection.hasNextPage()).toEqual(false);
            });

            it('aborts any previous request', function() {
                var requests = AjaxHelpers.requests(this);
                var response = {total: 35, results: []};

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

            describe('reset state', function() {
                beforeEach(function() {
                    this.collection.page = 2;
                    this.collection.totalCount = 35;
                    this.collection.latestModelsCount = 5;
                });

                it('resets state when performing new search', function() {
                    this.collection.performSearch('search string');
                    expect(this.collection.models.length).toEqual(0);
                    expect(this.collection.page).toEqual(0);
                    expect(this.collection.totalCount).toEqual(0);
                    expect(this.collection.latestModelsCount).toEqual(0);
                });

                it('resets state when canceling a search', function() {
                    this.collection.cancelSearch();
                    expect(this.collection.models.length).toEqual(0);
                    expect(this.collection.page).toEqual(0);
                    expect(this.collection.totalCount).toEqual(0);
                    expect(this.collection.latestModelsCount).toEqual(0);
                });
            });
        });


        describe('SearchRouter', function() {
            beforeEach(function() {
                this.router = new SearchRouter();
                this.onSearch = jasmine.createSpy('onSearch');
                this.router.on('search', this.onSearch);
            });

            it('has a search route', function() {
                expect(this.router.routes['search/:query']).toEqual('search');
            });

            it('triggers a search event', function() {
                var query = 'mercury';
                this.router.search(query);
                expect(this.onSearch).toHaveBeenCalledWith(query);
            });
        });


        describe('SearchItemView', function() {
            beforeEach(function() {
                this.model = new SearchResult({
                    location: ['section', 'subsection', 'unit'],
                    content_type: 'Video',
                    course_name: 'Course Name',
                    excerpt: 'A short excerpt.',
                    url: 'path/to/content'
                });

                this.seqModel = new SearchResult({
                    location: ['section', 'subsection'],
                    content_type: 'Sequence',
                    course_name: 'Course Name',
                    excerpt: 'A short excerpt.',
                    url: 'path/to/content'
                });

                this.item = new SearchItemView({
                    model: this.model,
                    template: courseSearchItemTemplate
                });
                this.item.render();
                this.seqItem = new SearchItemView({
                    model: this.seqModel,
                    template: courseSearchItemTemplate
                });
                this.seqItem.render();
            });

            it('rendersItem', function() {
                expect(this.item.$el).toHaveAttr('role', 'region');
                expect(this.item.$el).toHaveAttr('aria-label', 'search result');
                expect(this.item.$el).toContainElement('a[href="' + this.model.get('url') + '"]');
                expect(this.item.$el.find('.result-type i')).toHaveClass('fa-' + this.item.unitIcon());
                expect(this.item.$el.find('.result-excerpt')).toContainHtml(this.model.get('excerpt'));
                expect(this.item.$el.find('.result-link')).toContainHtml('section / subsection / unit');
            });

            it('rendersSequentialItem', function() {
                expect(this.seqItem.$el).toHaveAttr('role', 'region');
                expect(this.seqItem.$el).toHaveAttr('aria-label', 'search result');
                expect(this.seqItem.$el).toContainElement('a[href="' + this.seqModel.get('url') + '"]');
                expect(this.seqItem.$el.find('.result-type i')).toHaveClass('fa-' + this.seqItem.unitIcon());
                expect(this.seqItem.$el.find('.result-excerpt')).toBeEmpty();
                expect(this.seqItem.$el.find('.result-link')).toContainHtml('section / subsection');
            });

            it('logsSearchItemViewEvent', function() {
                this.model.collection = new SearchCollection([this.model], {course_id: 'edx101'});
                this.item.render();
                // Mock the redirect call
                spyOn(this.item, 'redirect').and.callFake(function() {});
                spyOn(Logger, 'log').and.returnValue($.Deferred().resolve());
                this.item.$el.find('a').trigger('click');
                expect(this.item.redirect).toHaveBeenCalled();
                this.item.$el.trigger('click');
                expect(this.item.redirect).toHaveBeenCalled();
            });
        });


        describe('SearchForm', function() {
            function trimsInputString() {
                var term = '    search string  ';
                $('.search-field').val(term);
                $('form').trigger('submit');
                expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
            }

            function doesSearch() {
                var term = '  search string  ';
                $('.search-field').val(term);
                this.form.doSearch(term);
                expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
                expect($('.search-field').val()).toEqual(term.trim());
                expect($('.search-field')).toHaveClass('is-active');
                expect($('.search-button')).toBeHidden();
                expect($('.cancel-button')).toBeVisible();
            }

            function triggersSearchEvent() {
                var term = 'search string';
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

            describe('SearchForm', function() {
                beforeEach(function() {
                    loadFixtures('course_search/fixtures/course_content_page.html');
                    this.form = new SearchForm({
                        el: '.search-bar'
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


        describe('SearchResultsView', function() {
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
                var searchResults = [{
                    location: ['section', 'subsection', 'unit'],
                    url: '/some/url/to/content',
                    content_type: 'text',
                    course_name: '',
                    excerpt: 'this is a short excerpt'
                }];
                this.collection.set(searchResults);
                this.collection.latestModelsCount = 1;
                this.collection.totalCount = 1;

                this.resultsView.render();
                expect(this.resultsView.$el.find('ol')[0]).toExist();
                expect(this.resultsView.$el.find('li').length).toEqual(1);
                expect(this.resultsView.$el).toContainHtml(
                    this.collection.totalCount +
                    ' result found for "' +
                    this.collection.searchTerm + '"'
                );
                expect(this.resultsView.$el).toContainHtml('this is a short excerpt');

                this.collection.set(searchResults);
                this.collection.totalCount = 2;
                this.resultsView.renderNext();
                expect(this.resultsView.$el.find('li').length).toEqual(2);
            }

            function showsMoreResultsLink() {
                this.collection.totalCount = 123;
                this.collection.hasNextPage = function() { return true; };
                this.resultsView.render();
                expect(this.resultsView.$el.find('a.search-load-next')[0]).toExist();

                this.collection.totalCount = 123;
                this.collection.hasNextPage = function() { return false; };
                this.resultsView.render();
                expect(this.resultsView.$el.find('a.search-load-next')[0]).not.toExist();
            }

            function triggersNextPageEvent() {
                var onNext = jasmine.createSpy('onNext');
                this.resultsView.on('next', onNext);
                this.collection.totalCount = 123;
                this.collection.hasNextPage = function() { return true; };
                this.resultsView.render();
                this.resultsView.$el.find('a.search-load-next').click();
                expect(onNext).toHaveBeenCalled();
            }

            function showsLoadMoreSpinner() {
                this.collection.totalCount = 123;
                this.collection.hasNextPage = function() { return true; };
                this.resultsView.render();
                expect(this.resultsView.$el.find('a.search-load-next .icon')).toBeHidden();
                this.resultsView.loadNext();
                // toBeVisible does not work with inline
                expect(this.resultsView.$el.find('a.search-load-next .icon')).toHaveCss({
                    display: 'inline'
                });
                this.resultsView.renderNext();
                expect(this.resultsView.$el.find('a.search-load-next .icon')).toBeHidden();
            }

            function beforeEachHelper(SearchResultsView) {
                var MockCollection = Backbone.Collection.extend({
                    hasNextPage: function() {},
                    latestModelsCount: 0,
                    pageSize: 20,
                    latestModels: function() {
                        return SearchCollection.prototype.latestModels.apply(this, arguments);
                    }
                });

                this.collection = new MockCollection();
                this.collection.searchTerm = 'demo';
                this.resultsView = new SearchResultsView({collection: this.collection});
            }

            describe('CourseSearchResultsView', function() {
                beforeEach(function() {
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

            describe('DashSearchResultsView', function() {
                beforeEach(function() {
                    loadFixtures('course_search/fixtures/dashboard_search_page.html');
                    beforeEachHelper.call(this, DashSearchResultsView);
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


        describe('SearchApp', function() {
            function showsLoadingMessage() {
                $('.search-field').val('search string');
                $('.search-button').trigger('click');
                expect(this.$searchResults).toBeVisible();
                expect(this.$searchResults).not.toBeEmpty();
            }

            function performsSearch() {
                var requests = AjaxHelpers.requests(this);
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
                            course_name: ''
                        }
                    }]
                });
                expect($('.search-info')).toExist();
                expect($('.search-result-list')).toBeVisible();
                expect(this.$searchResults.find('li').length).toEqual(1);
            }

            function showsErrorMessage() {
                var requests = AjaxHelpers.requests(this);
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
                var requests = AjaxHelpers.requests(this);
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
                var requests = AjaxHelpers.requests(this);
                var response = {
                    total: 1337,
                    access_denied_count: 12,
                    results: [{
                        data: {
                            location: ['section', 'subsection', 'unit'],
                            url: '/some/url/to/content',
                            content_type: 'text',
                            excerpt: 'this is a short excerpt',
                            course_name: ''
                        }
                    }]
                };
                var body;
                $('.search-field').val('query');
                $('.search-button').trigger('click');
                AjaxHelpers.respondWithJson(requests, response);
                expect(this.$searchResults.find('li').length).toEqual(1);
                expect($('.search-load-next')).toBeVisible();
                $('.search-load-next').trigger('click');
                body = requests[1].requestBody;
                expect(body).toContain('search_string=query');
                expect(body).toContain('page_index=1');
                AjaxHelpers.respondWithJson(requests, response);
                expect(this.$searchResults.find('li').length).toEqual(2);
            }

            function navigatesToSearch() {
                var requests = AjaxHelpers.requests(this);
                Backbone.history.start();
                Backbone.history.loadUrl('search/query');
                expect(requests[0].requestBody).toContain('search_string=query');
            }

            describe('CourseSearchApp', function() {
                beforeEach(function() {
                    var courseId = 'a/b/c';
                    loadFixtures('course_search/fixtures/course_content_page.html');
                    CourseSearchFactory({
                        courseId: courseId,
                        searchHeader: $('.search-bar')
                    });
                    spyOn(Backbone.history, 'navigate');
                    this.$contentElement = $('#course-content');
                    this.contentElementDisplayValue = 'table-cell';
                    this.$searchResults = $('.search-results');
                });

                afterEach(function() {
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

            describe('DashboardSearchApp', function() {
                beforeEach(function() {
                    loadFixtures('course_search/fixtures/dashboard_search_page.html');
                    DashboardSearchFactory();

                    spyOn(Backbone.history, 'navigate');
                    this.contentElementDisplayValue = 'block';
                    this.$searchResults = $('.search-results');
                });

                afterEach(function() {
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
                it('returns to course list', function() {
                    var requests = AjaxHelpers.requests(this);
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
                                course_name: ''
                            }
                        }]
                    });
                    $('.search-form .cancel-button').trigger('click');
                    expect(this.$searchResults).toBeHidden();
                    expect(this.$searchResults).toBeEmpty();
                });
            });

            describe('Course Search Results Page', function() {
                beforeEach(function() {
                    var courseId = 'a/b/c';
                    loadFixtures('course_search/fixtures/course_search_results_page.html');
                    CourseSearchFactory({
                        courseId: courseId,
                        searchHeader: $('.page-header-search')
                    });
                    spyOn(Backbone.history, 'navigate');
                    this.$contentElement = null;  // The search results page does not show over a content element
                    this.contentElementDisplayValue = 'table-cell';
                    this.$searchResults = $('.search-results');
                });

                afterEach(function() {
                    Backbone.history.stop();
                });

                it('shows loading message on search', showsLoadingMessage);
                it('performs search', performsSearch);
                it('shows an error message', showsErrorMessage);
                it('loads next page', loadsNextPage);
            });
        });
    });
});
