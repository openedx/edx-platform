define([
    'common/js/components/views/paging_header',
    'common/js/components/collections/paging_collection'
], function (PagingHeader, PagingCollection) {
        'use strict';
        describe('PagingHeader', function () {
            var pagingHeader,
                newCollection = function (size, perPage) {
                    var pageSize = 5,
                        results = _.map(_.range(size), function () { return {}; });
                    var collection = new PagingCollection(
                        {
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

            it('correctly displays which items are being viewed', function () {
                pagingHeader = new PagingHeader({
                    collection: newCollection(20, 5)
                }).render();
                expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing 1 through 5 of 20 items');
            });

            it('reports that all items are on the current page', function () {
                pagingHeader = new PagingHeader({
                    collection: newCollection(5, 5)
                }).render();
                expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing all 5 items');
            });

            it('reports that the page contains a single item', function () {
                pagingHeader = new PagingHeader({
                    collection: newCollection(1, 1)
                }).render();
                expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing 1 item');
            });

            it('supports different display names', function () {
                pagingHeader = new PagingHeader({
                    collection: newCollection(1, 1),
                    itemDisplayNameSingular: 'thing',
                    itemDisplayNamePlural: 'things'
                }).render();
                expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing 1 thing');
                pagingHeader = new PagingHeader({
                    collection: newCollection(2, 2),
                    itemDisplayNameSingular: 'thing',
                    itemDisplayNamePlural: 'things'
                }).render();
                expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Currently viewing all 2 things');
            });
        });
    });
