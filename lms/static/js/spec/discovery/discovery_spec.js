define([
    'jquery',
    'sinon',
    'backbone',
    'logger',
    'js/common_helpers/template_helpers',
    'js/discovery/app',
    'js/discovery/collection',
    'js/discovery/form',
    'js/discovery/result',
    'js/discovery/result_item_view',
    'js/discovery/result_list_view'
], function(
    $,
    Sinon,
    Backbone,
    Logger,
    TemplateHelpers,
    App,
    Collection,
    DiscoveryForm,
    ResultItem,
    ResultItemView,
    ResultListView

) {
    'use strict';

    var JSON_RESPONSE = {
        "total": 1,
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
        ]
    };

    describe('Collection', function () {

        beforeEach(function () {
            this.server = Sinon.fakeServer.create();
            this.collection = new Collection();

            this.onSearch = jasmine.createSpy('onSearch');
            this.collection.on('search', this.onSearch);

            this.onNext = jasmine.createSpy('onNext');
            this.collection.on('next', this.onNext);

            this.onError = jasmine.createSpy('onError');
            this.collection.on('error', this.onError);
        });

        afterEach(function () {
            this.server.restore();
        });

        it('sends a request and parses the json result', function () {
            this.collection.performSearch('search string');
            this.server.respondWith('POST', this.collection.url, [200, {}, JSON.stringify(JSON_RESPONSE)]);
            this.server.respond();

            expect(this.onSearch).toHaveBeenCalled();
            expect(this.collection.totalCount).toEqual(1);
            expect(this.collection.latestModels()[0].attributes).toEqual(JSON_RESPONSE.results[0].data);
            expect(this.collection.page).toEqual(0);
        });

        it('handles errors', function () {
            this.collection.performSearch('search string');
            this.server.respond();
            expect(this.onSearch).not.toHaveBeenCalled();
            expect(this.onError).toHaveBeenCalled();
            this.collection.loadNextPage();
            this.server.respond();
            expect(this.onSearch).not.toHaveBeenCalled();
            expect(this.onError).toHaveBeenCalled();
        });

        it('loads next page', function () {
            var response = { total: 35, results: [] };
            this.collection.loadNextPage();
            this.server.respond('POST', this.collection.url, [200, {}, JSON.stringify(response)]);
            expect(this.onNext).toHaveBeenCalled();
            expect(this.onError).not.toHaveBeenCalled();
        });

        it('sends correct paging parameters', function () {
            this.collection.performSearch('search string');
            var response = { total: 52, results: [] };
            this.server.respondWith('POST', this.collection.url, [200, {}, JSON.stringify(response)]);
            this.server.respond();
            this.collection.loadNextPage();
            this.server.respond();
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
            var response = { total: 35, access_denied_count: 5, results: [] };
            this.collection.performSearch('search string');
            this.server.respond('POST', this.collection.url, [200, {}, JSON.stringify(response)]);
            expect(this.collection.hasNextPage()).toEqual(true);
            this.collection.loadNextPage();
            this.server.respond();
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
            TemplateHelpers.installTemplates([
                'templates/discovery/not_found',
                'templates/discovery/error'
            ]);
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






});
