define([
    'underscore',
    'common/js/components/views/search_field',
    'common/js/components/collections/paging_collection',
    'common/js/spec_helpers/ajax_helpers'
], function (_, SearchFieldView, PagingCollection, AjaxHelpers) {
    'use strict';
    describe('SearchFieldView', function () {
        var searchFieldView,
            mockUrl = '/api/mock_collection';

        var newCollection = function (size, perPage) {
            var pageSize = 5,
                results = _.map(_.range(size), function (i) { return {foo: i}; });
            var collection = new PagingCollection(
                [],
                {
                    url: mockUrl,
                    count: results.length,
                    num_pages: results.length / pageSize,
                    current_page: 1,
                    start: 0,
                    results: _.first(results, perPage)
                },
                {parse: true}
            );
            collection.start = 0;
            collection.totalCount = results.length;
            return collection;
        };

        var createSearchFieldView = function (options) {
            options = _.extend(
                {
                    type: 'test',
                    collection: newCollection(5, 4),
                    el: $('.test-search')
                },
                options || {}
            );
            return new SearchFieldView(options);
        };

        beforeEach(function() {
            setFixtures('<section class="test-search"></section>');
        });

        it('correctly displays itself', function () {
            searchFieldView = createSearchFieldView().render();
            expect(searchFieldView.$('.search-field').val(), '');
            expect(searchFieldView.$('.action-clear')).toHaveClass('is-hidden');
        });

        it('can display with an initial search string', function () {
            searchFieldView = createSearchFieldView({
                searchString: 'foo'
            }).render();
            expect(searchFieldView.$('.search-field').val(), 'foo');
        });

        it('refreshes the collection when performing a search', function () {
            var requests = AjaxHelpers.requests(this);
            searchFieldView = createSearchFieldView().render();
            searchFieldView.$('.search-field').val('foo');
            searchFieldView.$('.action-search').click();
            AjaxHelpers.expectRequestURL(requests, mockUrl, {
                page: '1',
                page_size: '10',
                sort_order: '',
                text_search: 'foo'
            });
            AjaxHelpers.respondWithJson(requests, {
                count: 10,
                current_page: 1,
                num_pages: 1,
                start: 0,
                results: []
            });
            expect(searchFieldView.$('.search-field').val(), 'foo');
        });

        it('can clear the search', function () {
            var requests = AjaxHelpers.requests(this);
            searchFieldView = createSearchFieldView({
                searchString: 'foo'
            }).render();
            searchFieldView.$('.action-clear').click();
            AjaxHelpers.expectRequestURL(requests, mockUrl, {
                page: '1',
                page_size: '10',
                sort_order: '',
                text_search: ''
            });
            AjaxHelpers.respondWithJson(requests, {
                count: 10,
                current_page: 1,
                num_pages: 1,
                start: 0,
                results: []
            });
            expect(searchFieldView.$('.search-field').val(), '');
            expect(searchFieldView.$('.action-clear')).toHaveClass('is-hidden');
        });
    });
});
