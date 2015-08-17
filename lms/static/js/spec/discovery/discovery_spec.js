define([
    'jquery',
    'backbone',
    'logger',
    'common/js/spec_helpers/ajax_helpers',
    'common/js/spec_helpers/template_helpers',
    'js/discovery/app',
    'js/discovery/collection',
    'js/discovery/form',
    'js/discovery/result',
    'js/discovery/result_item_view',
    'js/discovery/result_list_view',
    'js/discovery/filter',
    'js/discovery/filters',
    'js/discovery/filter_bar_view',
    'js/discovery/filter_view',
    'js/discovery/search_facets_view',
    'js/discovery/facet_view',
    'js/discovery/facets_view'
], function(
    $,
    Backbone,
    Logger,
    AjaxHelpers,
    TemplateHelpers,
    App,
    Collection,
    DiscoveryForm,
    ResultItem,
    ResultItemView,
    ResultListView,
    FilterModel,
    FiltersCollection,
    FiltersBarView,
    FilterView,
    SearchFacetView,
    FacetView,
    FacetsView
) {
    'use strict';

    var JSON_RESPONSE = {
        "total": 365,
        "results": [
            {
                "data": {
                    "modes": [
                        "honor"
                    ],
                    "course": "edX/DemoX/Demo_Course",
                    "enrollment_start": "2015-04-21T00:00:00+00:00",
                    "number": "DemoX",
                    "content": {
                        "overview": " About This Course Include your long course description here.",
                        "display_name": "edX Demonstration Course",
                        "number": "DemoX"
                    },
                    "start": "1970-01-01T05:00:00+00:00",
                    "image_url": "/c4x/edX/DemoX/asset/images_course_image.jpg",
                    "org": "edX",
                    "id": "edX/DemoX/Demo_Course"
                }
            }
        ],
        "facets": {
            "org": {
                "total": 26,
                "terms": {
                    "edX1": 1,
                    "edX2": 1,
                    "edX3": 1,
                    "edX4": 1,
                    "edX5": 1,
                    "edX6": 1,
                    "edX7": 1,
                    "edX8": 1,
                    "edX9": 1,
                    "edX10": 1,
                    "edX11": 1,
                    "edX12": 1,
                    "edX13": 1,
                    "edX14": 1,
                    "edX15": 1,
                    "edX16": 1,
                    "edX17": 1,
                    "edX18": 1,
                    "edX19": 1,
                    "edX20": 1,
                    "edX21": 1,
                    "edX22": 1,
                    "edX23": 1,
                    "edX24": 1,
                    "edX25": 1,
                    "edX26": 1
                },
                "other": 0
            },
            "modes": {
                "total": 1,
                "terms": {
                    "honor": 1
                },
                "other": 0
            }
        }
    };

    var FACET_LIST = [
        {"type": "example1", "query": "search1"},
        {"type": "example2", "query": "search2"}
    ];

    var SEARCH_FILTER = {"type": "search_string", "query": "search3"};


    describe('Collection', function () {

        beforeEach(function () {
            this.collection = new Collection();

            this.onSearch = jasmine.createSpy('onSearch');
            this.collection.on('search', this.onSearch);

            this.onNext = jasmine.createSpy('onNext');
            this.collection.on('next', this.onNext);

            this.onError = jasmine.createSpy('onError');
            this.collection.on('error', this.onError);
        });

        it('sends a request and parses the json result', function () {
            var requests = AjaxHelpers.requests(this);
            this.collection.performSearch('search string');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect(this.onSearch).toHaveBeenCalled();
            expect(this.collection.totalCount).toEqual(365);
            expect(this.collection.latestModels()[0].attributes).toEqual(JSON_RESPONSE.results[0].data);
            expect(this.collection.page).toEqual(0);
        });

        it('handles errors', function () {
            var requests = AjaxHelpers.requests(this);
            this.collection.performSearch('search string');
            AjaxHelpers.respondWithError(requests);
            expect(this.onSearch).not.toHaveBeenCalled();
            expect(this.onError).toHaveBeenCalled();
            this.collection.loadNextPage();
            AjaxHelpers.respondWithError(requests);
            expect(this.onSearch).not.toHaveBeenCalled();
            expect(this.onError).toHaveBeenCalled();
        });

        it('loads next page', function () {
            var requests = AjaxHelpers.requests(this);
            var response = { total: 35, results: [] };
            this.collection.loadNextPage();
            AjaxHelpers.respondWithJson(requests, response);
            expect(this.onNext).toHaveBeenCalled();
            expect(this.onError).not.toHaveBeenCalled();
        });

        it('sends correct paging parameters', function () {
            var requests = AjaxHelpers.requests(this);
            var response = { total: 52, results: [] };
            this.collection.performSearch('search string');
            AjaxHelpers.respondWithJson(requests, response);
            this.collection.loadNextPage();
            AjaxHelpers.respondWithJson(requests, response);
            spyOn($, 'ajax');
            this.collection.loadNextPage();
            expect($.ajax.mostRecentCall.args[0].url).toEqual(this.collection.url);
            expect($.ajax.mostRecentCall.args[0].data).toEqual({
                search_string : 'search string',
                page_size : this.collection.pageSize,
                page_index : 2
            });
        });

        it('has next page', function () {
            var requests = AjaxHelpers.requests(this);
            var response = { total: 35, access_denied_count: 5, results: [] };
            this.collection.performSearch('search string');
            AjaxHelpers.respondWithJson(requests, response);
            expect(this.collection.hasNextPage()).toEqual(true);
            this.collection.loadNextPage();
            AjaxHelpers.respondWithJson(requests, response);
            expect(this.collection.hasNextPage()).toEqual(false);
        });

        it('resets state when performing new search', function () {
            this.collection.add(new ResultItem());
            expect(this.collection.length).toEqual(1);
            this.collection.performSearch('search string');
            expect(this.collection.length).toEqual(0);
            expect(this.collection.page).toEqual(0);
            expect(this.collection.totalCount).toEqual(0);
            expect(this.collection.latestModelsCount).toEqual(0);
        });

    });


    describe('ResultItem', function () {

        beforeEach(function () {
            this.result = new ResultItem();
        });

        it('has properties', function () {
            expect(this.result.get('modes')).toBeDefined();
            expect(this.result.get('course')).toBeDefined();
            expect(this.result.get('enrollment_start')).toBeDefined();
            expect(this.result.get('number')).toBeDefined();
            expect(this.result.get('content')).toEqual({
                display_name: '',
                number: '',
                overview: ''
            });
            expect(this.result.get('start')).toBeDefined();
            expect(this.result.get('image_url')).toBeDefined();
            expect(this.result.get('org')).toBeDefined();
            expect(this.result.get('id')).toBeDefined();
        });

    });


    describe('ResultItemView', function () {

        beforeEach(function () {
            TemplateHelpers.installTemplate('templates/discovery/result_item');
            this.item = new ResultItemView({
                model: new ResultItem(JSON_RESPONSE.results[0].data)
            });
        });

        it('renders correctly', function () {
            var data = this.item.model.attributes;
            this.item.render();
            expect(this.item.$el).toContainHtml(data.content.display_name);
            expect(this.item.$el).toContain('a[href="/courses/' + data.course + '/info"]');
            expect(this.item.$el).toContain('img[src="' + data.image_url + '"]');
            expect(this.item.$el.find('.course-name')).toContainHtml(data.org);
            expect(this.item.$el.find('.course-name')).toContainHtml(data.content.number);
            expect(this.item.$el.find('.course-name')).toContainHtml(data.content.display_name);
            expect(this.item.$el.find('.course-date')).toContainHtml('Jan 01, 1970');
        });

    });


    describe('DiscoveryForm', function () {

        beforeEach(function () {
            loadFixtures('js/fixtures/discovery.html');
            this.form = new DiscoveryForm();
            this.onSearch = jasmine.createSpy('onSearch');
            this.form.on('search', this.onSearch);
        });

        it('trims input string', function () {
            var term = '  search string  ';
            $('.discovery-input').val(term);
            $('form').trigger('submit');
            expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
        });

        it('handles calls to doSearch', function () {
            var term = '  search string  ';
            $('.discovery-input').val(term);
            this.form.doSearch(term);
            expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
            expect($('.discovery-input').val()).toEqual(term);
            expect($('#discovery-message')).toBeEmpty();
        });

        it('clears search', function () {
            $('.discovery-input').val('somethig');
            this.form.clearSearch();
            expect($('.discovery-input').val()).toEqual('');
        });

        it('shows/hides loading indicator', function () {
            this.form.showLoadingIndicator();
            expect($('#loading-indicator')).not.toHaveClass('hidden');
            this.form.hideLoadingIndicator();
            expect($('#loading-indicator')).toHaveClass('hidden');
        });

        it('shows messages', function () {
            this.form.showNotFoundMessage();
            expect($('#discovery-message')).not.toBeEmpty();
            this.form.showErrorMessage();
            expect($('#discovery-message')).not.toBeEmpty();
        });

    });

    describe('FilterBarView', function () {
        beforeEach(function () {
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplates(
                ['templates/discovery/filter_bar',
                'templates/discovery/filter']
            );
            this.filterBar = new FiltersBarView();
            this.onClear = jasmine.createSpy('onClear');
            this.filterBar.on('clear', this.onClear);
        });

        it('view searches for sent facet object', function () {
            expect(this.filterBar.$el.length).toBe(1);
            this.filterBar.addFilter(FACET_LIST[0]);
            expect(this.filterBar.$el.find('#clear-all-filters')).toBeVisible();
        });

        it('view searches for entered search string', function () {
            spyOn(this.filterBar, 'addFilter').andCallThrough();
            expect(this.filterBar.$el.length).toBe(1);
            this.filterBar.changeQueryFilter(SEARCH_FILTER.query);
            expect(this.filterBar.$el.find('#clear-all-filters')).toBeVisible();
            expect(this.filterBar.addFilter).toHaveBeenCalledWith(SEARCH_FILTER);
        });

        it('model cleans view on destruction correctly', function () {
            this.filterBar.addFilter(SEARCH_FILTER);
            var model = this.filterBar.collection.findWhere(SEARCH_FILTER);
            expect(this.filterBar.$el.find('.active-filter').length).toBe(1);
            model.cleanModelView();
            expect(this.filterBar.$el.find('.active-filter').length).toBe(0);
        });

        it('view removes all filters and hides bar if clear all', function () {
            spyOn(this.filterBar, 'clearAll').andCallThrough();
            this.filterBar.delegateEvents();
            this.filterBar.addFilter(SEARCH_FILTER);
            var clearAll = this.filterBar.$el.find('#clear-all-filters');
            expect(clearAll).toBeVisible();
            clearAll.trigger('click');
            expect(this.filterBar.clearAll).toHaveBeenCalled();
            expect(this.onClear).toHaveBeenCalled();
        });

        it('view hides bar if all filters removed', function () {
            spyOn(this.filterBar, 'clearFilter').andCallThrough();
            this.filterBar.delegateEvents();
            this.filterBar.addFilter(SEARCH_FILTER);
            var clearAll = this.filterBar.$el.find('#clear-all-filters');
            expect(clearAll).toBeVisible();
            var filter = this.filterBar.$el.find('li .discovery-button');
            filter.trigger('click');
            expect(this.filterBar.clearFilter).toHaveBeenCalled();
            expect(this.onClear).toHaveBeenCalled();
        });

        it('view changes query filter', function () {
            this.filterBar.addFilter(SEARCH_FILTER);
            var filter = $(this.filterBar.$el.find('li .discovery-button')[0]);
            expect(filter.text().trim()).toBe(SEARCH_FILTER.query);
            // Have to explicitly remove model because events not dispatched
            var model = this.filterBar.collection.findWhere(SEARCH_FILTER);
            model.cleanModelView();
            this.filterBar.changeQueryFilter(SEARCH_FILTER.query + '2');
            filter = $(this.filterBar.$el.find('li .discovery-button')[0]);
            expect(filter.text().trim()).toBe(SEARCH_FILTER.query + '2');
        });

        it('view returns correct search term', function () {
            this.filterBar.addFilter(SEARCH_FILTER);
            expect(this.filterBar.getSearchTerm()).toBe(SEARCH_FILTER.query);
        });

    });

    describe('SearchFacetView', function () {
        beforeEach(function () {
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplates([
                'templates/discovery/search_facet',
                'templates/discovery/search_facets_section',
                'templates/discovery/search_facets_list',
                'templates/discovery/more_less_links'
            ]);
            var facetsTypes = {org: 'Organization', modes: 'Course Type'};
            this.searchFacetView = new SearchFacetView(facetsTypes);
            this.searchFacetView.renderFacets(JSON_RESPONSE.facets);
            this.onAddFilter = jasmine.createSpy('onAddFilter');
            this.searchFacetView.on('addFilter', this.onAddFilter);
        });

        it('view expands more content on show more click', function () {
            var $showMore = this.searchFacetView.$el.find('.show-more');
            var $showLess = this.searchFacetView.$el.find('.show-less');
            var $ul = $showMore.parent('div').siblings('ul');
            expect($showMore).not.toHaveClass('hidden');
            expect($showLess).toHaveClass('hidden');
            expect($ul).toHaveClass('collapse');
            $showMore.trigger('click');
            expect($showMore).toHaveClass('hidden');
            expect($showLess).not.toHaveClass('hidden');
            expect($ul).not.toHaveClass('collapse');
        });

        it('view collapses content on show less click', function () {
            var $showMore = this.searchFacetView.$el.find('.show-more');
            var $showLess = this.searchFacetView.$el.find('.show-less');
            var $ul = $showMore.parent('div').siblings('ul');
            $showMore.trigger('click');
            expect($showMore).toHaveClass('hidden');
            expect($showLess).not.toHaveClass('hidden');
            expect($ul).not.toHaveClass('collapse');
            $showLess.trigger('click');
            expect($showMore).not.toHaveClass('hidden');
            expect($showLess).toHaveClass('hidden');
            expect($ul).toHaveClass('collapse');
        });

        it('view triggers addFilter event if facet is clicked', function () {
            this.searchFacetView.delegateEvents();
            var $facetLink = this.searchFacetView.$el.find('li [data-value="edX1"]');
            var $facet = $facetLink.parent('li');
            $facet.trigger('click');
            expect(this.onAddFilter).toHaveBeenCalledWith(
                {
                    type: $facet.data('facet'),
                    query: $facetLink.data('value'),
                    name : $facetLink.data('text')
                }
            );
        });

        it('re-render facets on second click', function () {
            // First search
            this.searchFacetView.delegateEvents();
            this.searchFacetView.renderFacets(JSON_RESPONSE.facets);
            expect(this.searchFacetView.facetViews.length).toBe(2);
            // Setup spy
            var customView = this.searchFacetView.facetViews[0];
            spyOn(customView, 'remove').andCallThrough();
            // Second search
            this.searchFacetView.renderFacets(JSON_RESPONSE.facets);
            expect(this.searchFacetView.facetViews.length).toBe(2);
            expect(customView.remove).toHaveBeenCalled();
        });

    });

    describe('ResultListView', function () {

        beforeEach(function () {
            jasmine.Clock.useMock();
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplate('templates/discovery/result_item');
            var collection = new Collection([JSON_RESPONSE.results[0].data]);
            collection.latestModelsCount = 1;
            this.view = new ResultListView({ collection: collection });
        });

        it('renders search results', function () {
            this.view.render();
            expect($('.courses-listing article').length).toEqual(1);
            expect($('.courses-listing .course-title')).toContainHtml('edX Demonstration Course');
            this.view.renderNext();
            expect($('.courses-listing article').length).toEqual(2);
        });

        it('scrolling triggers an event for next page', function () {
            this.onNext = jasmine.createSpy('onNext');
            this.view.on('next', this.onNext);
            spyOn(this.view.collection, 'hasNextPage').andCallFake(function () {
                return true;
            });
            this.view.render();
            window.scroll(0, $(document).height());
            $(window).trigger('scroll');
            jasmine.Clock.tick(500);
            expect(this.onNext).toHaveBeenCalled();

            // should not be triggered again (while it is loading)
            $(window).trigger('scroll');
            jasmine.Clock.tick(500);
            expect(this.onNext.calls.length).toEqual(1);
        });

    });


    describe('Discovery App', function () {

        beforeEach(function () {
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplates([
                'templates/discovery/result_item',
                'templates/discovery/filter',
                'templates/discovery/filter_bar',
                'templates/discovery/search_facet',
                'templates/discovery/search_facets_section',
                'templates/discovery/search_facets_list',
                'templates/discovery/more_less_links'
            ]);

            this.app = new App(
                Collection,
                DiscoveryForm,
                ResultListView,
                FiltersBarView,
                SearchFacetView
            );
        });

        it('performs search', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('test');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.courses-listing article').length).toEqual(1);
            expect($('.courses-listing .course-title')).toContainHtml('edX Demonstration Course');
            expect($('.active-filter').length).toBe(1);
        });

        it('loads more', function () {
            var requests = AjaxHelpers.requests(this);
            jasmine.Clock.useMock();
            $('.discovery-input').val('test');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.courses-listing article').length).toEqual(1);
            expect($('.courses-listing .course-title')).toContainHtml('edX Demonstration Course');
            window.scroll(0, $(document).height());
            $(window).trigger('scroll');
            jasmine.Clock.tick(500);
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.courses-listing article').length).toEqual(2);
        });

        it('displays not found message', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('asdfasdf');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, {});
            expect($('#discovery-message')).not.toBeEmpty();
            expect($('.courses-listing')).toBeEmpty();
        });

        it('displays error message', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('asdfasdf');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithError(requests, 404);
            expect($('#discovery-message')).not.toBeEmpty();
            expect($('.courses-listing')).toBeEmpty();
        });

        it('check filters and bar removed on clear all', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('test');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.active-filter').length).toBe(1);
            expect($('#filter-bar')).not.toHaveClass('hidden');
            $('#clear-all-filters').trigger('click');
            expect($('.active-filter').length).toBe(0);
            expect($('#filter-bar')).toHaveClass('hidden');
        });

        it('check filters and bar removed on last filter cleared', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('test');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.active-filter').length).toBe(1);
            var $filter = $('.active-filter');
            $filter.find('.discovery-button').trigger('click');
            expect($('.active-filter').length).toBe(0);
        });

        it('filter results by named facet', function () {
            var requests = AjaxHelpers.requests(this);
            $('.discovery-input').val('test');
            $('.discovery-submit').trigger('click');
            AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            expect($('.active-filter').length).toBe(1);
            var $facetLink = $('.search-facets li [data-value="edX1"]');
            var $facet = $facetLink.parent('li');
            $facet.trigger('click');
            expect($('.active-filter').length).toBe(2);
            expect($('.active-filter [data-value="edX1"]').length).toBe(1);
            expect($('.active-filter [data-value="edX1"]').text().trim()).toBe("edX_1");
        });

    });



});
