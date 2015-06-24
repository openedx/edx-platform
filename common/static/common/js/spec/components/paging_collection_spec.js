define(['jquery',
        'backbone',
        'underscore',
        'common/js/components/collections/paging_collection',
        'common/js/spec_helpers/ajax_helpers',
        'common/js/spec_helpers/spec_helpers'
    ],
    function ($, Backbone, _, PagingCollection, AjaxHelpers, SpecHelpers) {
        'use strict';

        describe('PagingCollection', function () {
            var collection,
                requests,
                server = {
                    isZeroIndexed: false,
                    count: 43,
                    respond: function () {
                        var url = requests[requests.length - 1].url;
                        var page = parseInt(url.match(/page=(\d+)/)[1], 10);
                        var page_size = parseInt(url.match(/page_size=(\d+)/)[1]);
                        var page_count = Math.ceil(this.count / page_size);

                        // Make zeroPage consistently start at zero for ease of calculation
                        var zeroPage = page - (this.isZeroIndexed ? 0 : 1);
                        if (zeroPage < 0 || zeroPage > page_count) {
                            AjaxHelpers.respondWithError(requests, 404, {}, requests.length - 1);
                        } else {
                            AjaxHelpers.respondWithJson(requests, {
                                'count': this.count,
                                'current_page': page,
                                'num_pages': page_count,
                                'start': zeroPage * page_size,
                                'results': []
                            }, requests.length - 1);
                        }
                    }
                };

            beforeEach(function () {
                collection = new PagingCollection();
                collection.perPage = 10;
                requests = AjaxHelpers.requests(this);
                server.isZeroIndexed = false;
                server.count = 43;
            });

            it('can register sortable fields', function () {
                collection.registerSortableField('test_field', 'Test Field');
                expect('test_field' in collection.sortableFields).toBe(true);
                expect(collection.sortableFields['test_field'].displayName).toBe('Test Field');
            });

            it('can register filterable fields', function () {
                collection.registerFilterableField('test_field', 'Test Field');
                expect('test_field' in collection.filterableFields).toBe(true);
                expect(collection.filterableFields['test_field'].displayName).toBe('Test Field');
            });

            it('can set the sort field and get the display name', function () {
                collection.registerSortableField('test_field', 'Test Field');
                collection.setSortField('test_field', false);
                expect(requests.length).toBe(1);
                expect(collection.sortField).toBe('test_field');
                expect(collection.sortDisplayName()).toBe('Test Field');
            });

            it('can set the filter field and get the display name', function () {
                collection.registerFilterableField('test_field', 'Test Field');
                collection.setFilterField('test_field');
                expect(requests.length).toBe(1);
                expect(collection.filterField).toBe('test_field');
                expect(collection.filterDisplayName()).toBe('Test Field');
            });

            it('can set the sort direction', function () {
                collection.setSortDirection(PagingCollection.SortDirection.ASCENDING);
                expect(requests.length).toBe(1);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.ASCENDING);
                collection.setSortDirection(PagingCollection.SortDirection.DESCENDING);
                expect(requests.length).toBe(2);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.DESCENDING);
            });

            it('can toggle the sort direction when setting the sort field', function () {
                collection.registerSortableField('test_field', 'Test Field');
                collection.registerSortableField('test_field_2', 'Test Field 2');
                collection.setSortField('test_field', true);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.DESCENDING);
                collection.setSortField('test_field', true);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.ASCENDING);
                collection.setSortField('test_field', true);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.DESCENDING);
                collection.setSortField('test_field_2', true);
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.DESCENDING);
            });

            it('queries with page, page_size, and sort_order parameters when zero indexed', function () {
                collection.isZeroIndexed = true;
                collection.perPage = 5;
                collection.sortField = 'test_field';
                collection.setPage(3);
                expect(requests[0].url).toContain('page=2');
                expect(requests[0].url).toContain('page_size=5');
                expect(requests[0].url).toContain('sort_order=test_field');
            });

            it('queries with page, page_size, and sort_order parameters when one indexed', function () {
                collection.isZeroIndexed = false;
                collection.perPage = 5;
                collection.sortField = 'test_field';
                collection.setPage(3);
                expect(requests[0].url).toContain('page=3');
                expect(requests[0].url).toContain('page_size=5');
                expect(requests[0].url).toContain('sort_order=test_field');
            });

            SpecHelpers.withConfiguration({
                'using a zero indexed collection': [true],
                'using a one indexed collection': [false]
            }, function (isZeroIndexed) {
                collection.isZeroIndexed = isZeroIndexed;
                server.isZeroIndexed = isZeroIndexed;
            }, function () {
                describe('setPage', function() {
                    it('triggers a reset event when the page changes successfully', function () {
                        var resetTriggered = false;
                        collection.on('reset', function () { resetTriggered = true; });
                        collection.setPage(3);
                        server.respond();
                        expect(resetTriggered).toBe(true);
                    });

                    it('triggers an error event when the requested page is out of range', function () {
                        var errorTriggered = false;
                        collection.on('error', function () { errorTriggered = true; });
                        collection.setPage(17);
                        server.respond();
                        expect(errorTriggered).toBe(true);
                    });

                    it('triggers an error event if the server responds with a 500', function () {
                        var errorTriggered = false;
                        collection.on('error', function () { errorTriggered = true; });
                        collection.setPage(3);
                        AjaxHelpers.respondWithError(requests, 500, {}, requests.length - 1);
                        expect(errorTriggered).toBe(true);
                    });
                });

                describe('currentOneIndexPage', function () {
                    it('returns the correct page', function () {
                        collection.setPage(1);
                        server.respond();
                        expect(collection.currentOneIndexPage()).toBe(1);
                        collection.setPage(3);
                        server.respond();
                        expect(collection.currentOneIndexPage()).toBe(3);
                    });
                });

                describe('hasNextPage', function () {
                    SpecHelpers.withData(
                        {
                            'returns false for a single page': [1, 3, false],
                            'returns true on the first page': [1, 43, true],
                            'returns true on the penultimate page': [4, 43, true],
                            'returns false on the last page': [5, 43, false]
                        },
                        function (page, count, result) {
                            server.count = count;
                            collection.setPage(page);
                            server.respond();
                            expect(collection.hasNextPage()).toBe(result);
                        }
                    );
                });

                describe('hasPreviousPage', function () {
                    SpecHelpers.withData(
                        {
                            'returns false for a single page': [1, 3, false],
                            'returns true on the last page': [5, 43, true],
                            'returns true on the second page': [2, 43, true],
                            'returns false on the first page': [1, 43, false]
                        },
                        function (page, count, result) {
                            server.count = count;
                            collection.setPage(page);
                            server.respond();
                            expect(collection.hasPreviousPage()).toBe(result);
                        }
                    );
                });

                describe('nextPage', function () {
                    SpecHelpers.withData(
                        {
                            'advances to the next page': [2, 43, 3],
                            'silently fails on the last page': [5, 43, 5]
                        },
                        function (page, count, newPage) {
                            server.count = count;
                            collection.setPage(page);
                            server.respond();
                            expect(collection.currentOneIndexPage()).toBe(page);
                            collection.nextPage();
                            if (requests.length > 1) {
                                server.respond();
                            }
                            expect(collection.currentOneIndexPage()).toBe(newPage);
                        }
                    );
                });

                describe('previousPage', function () {
                    SpecHelpers.withData(
                        {
                            'moves to the previous page': [2, 43, 1],
                            'silently fails on the first page': [1, 43, 1]
                        },
                        function (page, count, newPage) {
                            server.count = count;
                            collection.setPage(page);
                            server.respond();
                            expect(collection.currentOneIndexPage()).toBe(page);
                            collection.previousPage();
                            if (requests.length > 1) {
                                server.respond();
                            }
                            expect(collection.currentOneIndexPage()).toBe(newPage);
                        }
                    )
                });
            });
        });
    }
);
