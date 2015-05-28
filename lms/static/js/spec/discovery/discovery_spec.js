define([
    'jquery',
    'backbone',
    'logger',
    'common/js/spec_helpers/ajax_helpers',
    'common/js/spec_helpers/template_helpers',
    'js/discovery/app',
    'js/discovery/collections/filters',
    'js/discovery/models/course_card',
    'js/discovery/models/course_discovery',
    'js/discovery/models/facet_option',
    'js/discovery/models/filter',
    'js/discovery/models/search_state',
    'js/discovery/views/course_card',
    'js/discovery/views/courses_listing',
    'js/discovery/views/filter_bar',
    'js/discovery/views/filter_label',
    'js/discovery/views/refine_sidebar',
    'js/discovery/views/search_form'
], function(
    $,
    Backbone,
    Logger,
    AjaxHelpers,
    TemplateHelpers,
    App,
    Filters,
    CourseCard,
    CourseDiscovery,
    FacetOption,
    Filter,
    SearchState,
    CourseCardView,
    CoursesListing,
    FilterBar,
    FilterLabel,
    RefineSidebar,
    SearchForm
) {
    'use strict';

    describe('Course Discovery', function () {

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

        describe('models.Filter', function () {

            beforeEach(function () {
                this.filter = new Filter();
            });

            it('has properties', function () {
                expect(this.filter.get('type')).toBeDefined();
                expect(this.filter.get('query')).toBeDefined();
                expect(this.filter.get('name')).toBeDefined();
            });

        });


        describe('collections.Filters', function () {

            beforeEach(function () {
                this.filters = new Filters([
                    { type: 'org', query: 'edX', name: 'edX'},
                    { type: 'language', query: 'en', name: 'English'}
                ]);
            });

            it('converts to a dictionary', function () {
                expect(this.filters.getTerms()).toEqual({
                    org: 'edX',
                    language: 'en'
                });
            });

        });


        describe('models.CourseCard', function () {

            beforeEach(function () {
                this.card = new CourseCard();
            });

            it('has properties', function () {
                expect(this.card.get('modes')).toBeDefined();
                expect(this.card.get('course')).toBeDefined();
                expect(this.card.get('enrollment_start')).toBeDefined();
                expect(this.card.get('number')).toBeDefined();
                expect(this.card.get('content')).toEqual({
                    display_name: '',
                    number: '',
                    overview: ''
                });
                expect(this.card.get('start')).toBeDefined();
                expect(this.card.get('image_url')).toBeDefined();
                expect(this.card.get('org')).toBeDefined();
                expect(this.card.get('id')).toBeDefined();
            });

        });


        describe('models.FacetOption', function () {

            beforeEach(function () {
                this.filter = new FacetOption();
            });

            it('has properties', function () {
                expect(this.filter.get('facet')).toBeDefined();
                expect(this.filter.get('term')).toBeDefined();
                expect(this.filter.get('count')).toBeDefined();
                expect(this.filter.get('selected')).toBeDefined();
            });

        });


        describe('models.CourseDiscovery', function () {

            beforeEach(function () {
                var requests = AjaxHelpers.requests(this);
                this.discovery = new CourseDiscovery();
                this.discovery.fetch();
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
            });

            it('parses server response', function () {
                expect(this.discovery.courseCards.length).toBe(1);
                expect(this.discovery.facetOptions.length).toBe(27);
            });

            it('resets collections', function () {
                this.discovery.reset();
                expect(this.discovery.courseCards.length).toBe(0);
                expect(this.discovery.facetOptions.length).toBe(0);
            });

            it('returns latest course cards', function () {
                var latest = this.discovery.latest();
                expect(latest.length).toBe(1);
            });

        });


        describe('models.SearchState', function () {

            beforeEach(function () {
                this.search = new SearchState();
                this.onSearch = jasmine.createSpy('onSearch');
                this.onNext = jasmine.createSpy('onNext');
                this.onError = jasmine.createSpy('onError');
                this.search.on('search', this.onSearch);
                this.search.on('next', this.onNext);
                this.search.on('error', this.onError);
            });

            it('perform search', function () {
                var requests = AjaxHelpers.requests(this);
                this.search.performSearch('dummy');
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
                expect(this.onSearch).toHaveBeenCalledWith('dummy', 365);
                expect(this.search.discovery.courseCards.length).toBe(1);
                this.search.refineSearch({ modes: 'honor' });
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
                expect(this.onSearch).toHaveBeenCalledWith('dummy', 365);
            });

            it('returns an error', function () {
                var requests = AjaxHelpers.requests(this);
                this.search.performSearch('');
                AjaxHelpers.respondWithError(requests, 500);
                expect(this.onError).toHaveBeenCalled();
            });

            it('loads next page', function () {
                var requests = AjaxHelpers.requests(this);
                this.search.performSearch('dummy');
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
                this.search.loadNextPage();
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
                expect(this.onNext).toHaveBeenCalled();
            });

            it('shows all results when there are none', function () {
                var requests = AjaxHelpers.requests(this);
                this.search.performSearch('dummy', { modes: 'SomeOption' });
                // no results
                AjaxHelpers.respondWithJson(requests, { total: 0 });
                expect(this.onSearch).not.toHaveBeenCalled();
                // there should be another Ajax call to fetch all courses
                AjaxHelpers.respondWithJson(requests, JSON_RESPONSE);
                expect(this.onSearch).toHaveBeenCalledWith('dummy', 0);
                // new search
                this.search.performSearch('something');
                // no results
                AjaxHelpers.respondWithJson(requests, { total: 0 });
                // should load cached results
                expect(this.onSearch).toHaveBeenCalledWith('dummy', 0);
            });

        });


        describe('views.CourseCard', function () {

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/discovery/course_card');
                this.view = new CourseCardView({
                    model: new CourseCard(JSON_RESPONSE.results[0].data)
                });
                this.view.render();
            });

            it('renders', function () {
                var data = this.view.model.attributes;
                expect(this.view.$el).toContainHtml(data.content.display_name);
                expect(this.view.$el).toContain('a[href="/courses/' + data.course + '/about"]');
                expect(this.view.$el).toContain('img[src="' + data.image_url + '"]');
                expect(this.view.$el.find('.course-name')).toContainHtml(data.org);
                expect(this.view.$el.find('.course-name')).toContainHtml(data.content.number);
                expect(this.view.$el.find('.course-name')).toContainHtml(data.content.display_name);
                expect(this.view.$el.find('.course-date')).toContainHtml('Jan 01, 1970');
            });

        });


        describe('views.CoursesListing', function () {

            beforeEach(function () {
                jasmine.Clock.useMock();
                loadFixtures('js/fixtures/discovery.html');
                TemplateHelpers.installTemplate('templates/discovery/course_card');
                var collection = new Backbone.Collection(
                    [JSON_RESPONSE.results[0].data],
                    { model: CourseCard }
                );
                var mock = {
                    collection: collection,
                    latest: function () { return this.collection.last(20); }
                }
                this.view = new CoursesListing({ model: mock });
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


        describe('views.FilterLabel', function () {

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/discovery/filter');
                var filter = new Filter({
                    type: 'language',
                    query: 'en',
                    name: 'English'
                });
                this.view = new FilterLabel({model: filter});
                this.view.render();
            });

            it('renders', function () {
                var data = this.view.model.attributes;
                expect(this.view.$el.find('button')).toHaveData('value', 'en');
                expect(this.view.$el.find('button')).toHaveData('type', 'language');
                expect(this.view.$el).toContainHtml(data.name);
            });

            it('renders changes', function () {
                this.view.model.set('query', 'es');
                expect(this.view.$el.find('button')).toHaveData('value', 'es');
            });

            it('removes itself', function () {
                // simulate removing from collection
                this.view.model.trigger('remove');
                expect(this.view.$el).not.toExist();
            });

        });


        describe('views.FilterBar', function () {

            beforeEach(function () {
                loadFixtures('js/fixtures/discovery.html');
                TemplateHelpers.installTemplates([
                    'templates/discovery/filter',
                    'templates/discovery/filter_bar'
                ]);
                this.filters = new Filters();
                this.filterBar = new FilterBar({ collection: this.filters });
                this.filters.add({
                    type: 'org',
                    query: 'edX',
                    name: 'edX'
                });
            });

            it('adds filter', function () {
                expect(this.filterBar.$el.find('button')).toHaveData('type', 'org');
            });

            it('removes filter', function () {
                this.filters.remove('org');
                expect(this.filterBar.$el.find('ul')).toBeEmpty();
                expect(this.filterBar.$el).toHaveClass('slide-up');
            });

            it('resets filters', function () {
                this.filters.reset();
                expect(this.filterBar.$el.find('ul')).toBeEmpty();
                expect(this.filterBar.$el).toHaveClass('slide-up');
            });

            it('triggers events', function () {
                this.onClearFilter = jasmine.createSpy('onClearFilter');
                this.onClearAll = jasmine.createSpy('onClearAll');
                this.filterBar.on('clearFilter', this.onClearFilter);
                this.filterBar.on('clearAll', this.onClearAll);
                this.filterBar.$el.find('button').click();
                expect(this.onClearFilter).toHaveBeenCalledWith('org');
                this.filterBar.$el.find('#clear-all-filters').click();
                expect(this.onClearAll).toHaveBeenCalled();
            });

        });


        describe('views.RefineSidebar', function () {

            beforeEach(function () {
                loadFixtures('js/fixtures/discovery.html');
                TemplateHelpers.installTemplates([
                    'templates/discovery/facet',
                    'templates/discovery/facet_option'
                ]);
                this.facetOptions = new Backbone.Collection([], { model: FacetOption });
                this.facetOptions.add([
                    { facet: 'language', term: 'es', count: 12 },
                    { facet: 'language', term: 'en', count: 10 },
                    { facet: 'modes', term: 'honor', count: 2, selected: true }
                ]);
                this.sidebar = new RefineSidebar({ collection: this.facetOptions });
                this.sidebar.render();

            });

            it('styles active filter', function () {
                expect(this.sidebar.$el.find('button.selected')).toHaveData('facet', 'modes');
            });

            it('styles active filter', function () {
                this.onSelect = jasmine.createSpy('onSelect');
                this.sidebar.on('selectOption', this.onSelect);
                this.sidebar.$el.find('button[data-value="en"]').click();
                expect(this.onSelect).toHaveBeenCalledWith('language', 'en', 'English');
            });

            it('expands and collapses facet', function () {
                var options = _.range(20).map(function (number) {
                    return { facet: 'org', term: 'test' + number, count: 1 };
                });
                this.facetOptions.reset(options);
                this.sidebar.render();
                this.sidebar.$el.find('.show-more').click();
                expect(this.sidebar.$el.find('ul.facet-list')).not.toHaveClass('collapse');
                expect(this.sidebar.$el.find('.show-more')).toHaveClass('hidden');
                this.sidebar.$el.find('.show-less').click();
                expect(this.sidebar.$el.find('ul.facet-list')).toHaveClass('collapse');
                expect(this.sidebar.$el.find('.show-less')).toHaveClass('hidden');
            });

        });


        describe('views.SearchForm', function () {

            beforeEach(function () {
                loadFixtures('js/fixtures/discovery.html');
                this.form = new SearchForm();
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
                expect($('.discovery-input').val()).toBe(term);
                expect($('#discovery-message')).toBeEmpty();
            });

            it('clears search', function () {
                $('.discovery-input').val('somethig');
                this.form.clearSearch();
                expect($('.discovery-input').val()).toBe('');
            });

            it('shows/hides loading indicator', function () {
                this.form.showLoadingIndicator();
                expect($('#loading-indicator')).not.toHaveClass('hidden');
                this.form.hideLoadingIndicator();
                expect($('#loading-indicator')).toHaveClass('hidden');
            });

            it('shows messages', function () {
                this.form.showFoundMessage(123);
                expect($('#discovery-message')).toContainHtml(123);
                this.form.showNotFoundMessage();
                expect($('#discovery-message')).not.toBeEmpty();
                this.form.showErrorMessage();
                expect($('#discovery-message')).not.toBeEmpty();
            });

        });


        describe('app', function () {

            beforeEach(function () {
                loadFixtures('js/fixtures/discovery.html');
                TemplateHelpers.installTemplates([
                    'templates/discovery/course_card',
                    'templates/discovery/facet',
                    'templates/discovery/facet_option',
                    'templates/discovery/filter',
                    'templates/discovery/filter_bar'
                ]);
                this.app = new App();
            });

            it('does search', function () {
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
                expect($('#filter-bar')).not.toHaveClass('slide-up');
                $('#clear-all-filters').trigger('click');
                expect($('.active-filter').length).toBe(0);
                expect($('#filter-bar')).toHaveClass('slide-up');
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
                $('.search-facets li [data-value="edX1"]').trigger('click');
                expect($('.active-filter').length).toBe(2);
                expect($('.active-filter [data-value="edX1"]').length).toBe(1);
                $('.search-facets li [data-value="edX1"]').trigger('click');
                expect($('.active-filter [data-value="edX1"]').length).toBe(0);
            });

        });

    });

});
