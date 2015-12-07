define(['jquery',
        'backbone',
        'underscore',
        'URI',
        'common/js/components/collections/paging_collection',
        'common/js/spec_helpers/ajax_helpers',
        'common/js/spec_helpers/spec_helpers'
    ],
    function ($, Backbone, _, URI, PagingCollection, AjaxHelpers, SpecHelpers) {
        'use strict';

        describe('PagingCollection', function () {
            var collection;
            var server = {
                isZeroIndexed: false,
                count: 43,
                respond: function (requests) {
                    var request = AjaxHelpers.currentRequest(requests),
                        params = (new URI(request.url)).query(true),
                        page = parseInt(params['page'], 10),
                        page_size = parseInt(params['page_size'], 10),
                        page_count = Math.ceil(this.count / page_size);

                    // Make zeroPage consistently start at zero for ease of calculation
                    var zeroPage = page - (this.isZeroIndexed ? 0 : 1);
                    if (zeroPage < 0 || zeroPage > page_count) {
                        AjaxHelpers.respondWithError(requests, 404);
                    } else {
                        AjaxHelpers.respondWithJson(requests, {
                            'count': this.count,
                            'current_page': page,
                            'num_pages': page_count,
                            'start': zeroPage * page_size,
                            'results': []
                        });
                    }
                }
            };
            var assertQueryParams = function (requests, params) {
                var request = AjaxHelpers.currentRequest(requests),
                    urlParams = (new URI(request.url)).query(true);
                _.each(params, function (value, key) {
                    expect(urlParams[key]).toBe(value);
                });
            };

            beforeEach(function () {
                collection = new PagingCollection();
                collection.perPage = 10;
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

            it('sets the sort field based on the server response', function () {
                var sort_order = 'my_sort_order';
                collection = new PagingCollection({sort_order: sort_order}, {parse: true});
                expect(collection.sortField).toBe(sort_order);
            });

            it('can set the sort field', function () {
                var requests = AjaxHelpers.requests(this);
                collection.registerSortableField('test_field', 'Test Field');
                collection.setSortField('test_field', false);
                collection.refresh();
                assertQueryParams(requests, {'sort_order': 'test_field'});
                expect(collection.sortField).toBe('test_field');
                expect(collection.sortDisplayName()).toBe('Test Field');
            });

            it('can set the filter field', function () {
                collection.registerFilterableField('test_field', 'Test Field');
                collection.setFilterField('test_field');
                collection.refresh();
                // The default implementation does not send any query params for filtering
                expect(collection.filterField).toBe('test_field');
                expect(collection.filterDisplayName()).toBe('Test Field');
            });

            it('can set the sort direction', function () {
                collection.setSortDirection(PagingCollection.SortDirection.ASCENDING);
                // The default implementation does not send any query params for sort direction
                expect(collection.sortDirection).toBe(PagingCollection.SortDirection.ASCENDING);
                collection.setSortDirection(PagingCollection.SortDirection.DESCENDING);
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

            SpecHelpers.withData({
                'queries with page, page_size, and sort_order parameters when zero indexed': [true, 2],
                'queries with page, page_size, and sort_order parameters when one indexed': [false, 3],
            }, function (isZeroIndexed, page) {
                var requests = AjaxHelpers.requests(this);
                collection.isZeroIndexed = isZeroIndexed;
                collection.perPage = 5;
                collection.sortField = 'test_field';
                collection.setPage(3);
                assertQueryParams(requests, {'page': page.toString(), 'page_size': '5', 'sort_order': 'test_field'});
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
                        var requests = AjaxHelpers.requests(this),
                            resetTriggered = false;
                        collection.on('reset', function () { resetTriggered = true; });
                        collection.setPage(3);
                        server.respond(requests);
                        expect(resetTriggered).toBe(true);
                    });

                    it('triggers an error event when the requested page is out of range', function () {
                        var requests = AjaxHelpers.requests(this),
                            errorTriggered = false;
                        collection.on('error', function () { errorTriggered = true; });
                        collection.setPage(17);
                        server.respond(requests);
                        expect(errorTriggered).toBe(true);
                    });

                    it('triggers an error event if the server responds with a 500', function () {
                        var requests = AjaxHelpers.requests(this),
                            errorTriggered = false;
                        collection.on('error', function () { errorTriggered = true; });
                        collection.setPage(2);
                        expect(collection.getPage()).toBe(2);
                        server.respond(requests);
                        collection.setPage(3);
                        AjaxHelpers.respondWithError(requests, 500);
                        expect(errorTriggered).toBe(true);
                        expect(collection.getPage()).toBe(2);
                    });
                });

                describe('getPage', function () {
                    it('returns the correct page', function () {
                        var requests = AjaxHelpers.requests(this);
                        collection.setPage(1);
                        server.respond(requests);
                        expect(collection.getPage()).toBe(1);
                        collection.setPage(3);
                        server.respond(requests);
                        expect(collection.getPage()).toBe(3);
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
                            var requests = AjaxHelpers.requests(this);
                            server.count = count;
                            collection.setPage(page);
                            server.respond(requests);
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
                            var requests = AjaxHelpers.requests(this);
                            server.count = count;
                            collection.setPage(page);
                            server.respond(requests);
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
                            var requests = AjaxHelpers.requests(this);
                            server.count = count;
                            collection.setPage(page);
                            server.respond(requests);
                            expect(collection.getPage()).toBe(page);
                            collection.nextPage();
                            if (requests.length > 1) {
                                server.respond(requests);
                            }
                            expect(collection.getPage()).toBe(newPage);
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
                            var requests = AjaxHelpers.requests(this);
                            server.count = count;
                            collection.setPage(page);
                            server.respond(requests);
                            expect(collection.getPage()).toBe(page);
                            collection.previousPage();
                            if (requests.length > 1) {
                                server.respond(requests);
                            }
                            expect(collection.getPage()).toBe(newPage);
                        }
                    );
                });
            });
        });
    }
);
