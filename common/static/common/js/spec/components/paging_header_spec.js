define([
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'common/js/components/views/paging_header'
], function(_, PagingCollection, PagingHeader) {
    'use strict';
    describe('PagingHeader', function() {
        var pagingHeader,
            newCollection = function(size, perPage) {
                var pageSize = 5,
                    results = _.map(_.range(size), function(i) { return {foo: i}; });
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
            },
            sortableHeader = function(sortable) {
                var collection = newCollection(5, 4);
                collection.registerSortableField('foo', 'Display Name');
                return new PagingHeader({
                    collection: collection,
                    showSortControls: _.isUndefined(sortable) ? true : sortable
                });
            };

        it('correctly displays which items are being viewed', function() {
            pagingHeader = new PagingHeader({
                collection: newCollection(20, 5)
            }).render();
            expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Showing 1-5 out of 20 total');
        });

        it('reports that all items are on the current page', function() {
            pagingHeader = new PagingHeader({
                collection: newCollection(5, 5)
            }).render();
            expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Showing 1-5 out of 5 total');
        });

        it('reports that the page contains a single item', function() {
            pagingHeader = new PagingHeader({
                collection: newCollection(1, 1)
            }).render();
            expect(pagingHeader.$el.find('.search-count').text())
                    .toContain('Showing 1 out of 1 total');
        });

        it('optionally shows sorting controls', function() {
            pagingHeader = sortableHeader().render();
            expect(pagingHeader.$el.find('.listing-sort').text())
                    .toMatch(/Sorted by\s+Display Name/);
        });

        it('does not show sorting controls if the `showSortControls` option is not passed', function() {
            pagingHeader = sortableHeader(false).render();
            expect(pagingHeader.$el.text()).not.toContain('Sorted by');
        });
    });
});
