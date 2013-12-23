define([ "jquery", "js/spec/create_sinon", "URI",
    "js/views/paging", "js/views/paging_header", "js/views/paging_footer",
    "js/models/asset", "js/collections/asset" ],
    function ($, create_sinon, URI, PagingView, PagingHeader, PagingFooter, AssetModel, AssetCollection) {

        var feedbackTpl = readFixtures('system-feedback.underscore'),
            assetLibraryTpl = readFixtures('asset-library.underscore'),
            assetTpl = readFixtures('asset.underscore'),
            pagingHeaderTpl = readFixtures('paging-header.underscore'),
            pagingFooterTpl = readFixtures('paging-footer.underscore');

        var createMockAsset = function(index) {
            var id = 'asset_' + index;
            return {
                id: id,
                display_name: id,
                url: id
            };
        };

        var mockFirstPage = {
            assets: [
                createMockAsset(1),
                createMockAsset(2),
                createMockAsset(3)
            ],
            pageSize: 3,
            totalCount: 4,
            page: 0,
            start: 0,
            end: 2
        };
        var mockSecondPage = {
            assets: [
                createMockAsset(4)
            ],
            pageSize: 3,
            totalCount: 4,
            page: 1,
            start: 3,
            end: 4
        };
        var mockEmptyPage = {
            assets: [],
            pageSize: 3,
            totalCount: 0,
            page: 0,
            start: 0,
            end: 0
        };

        var respondWithMockAssets = function(requests, requestIndex) {
            requestIndex = requestIndex || requests.length - 1;
            var request = requests[requestIndex];
            var url = new URI(request.url);
            var page = url.query(true).page;
            var response = page === "0" ? mockFirstPage : mockSecondPage;
            create_sinon.respondWithJson(requests, response, requestIndex);
        };

        var MockPagingView = PagingView.extend({
            renderPageItems: function() {}
        });

        describe("PagingView", function () {
            var requests,
                pagingView;

            beforeEach(function () {
                var assets = new AssetCollection();
                assets.url = "assets_url";
                pagingView = new MockPagingView({collection: assets});
                setFixtures($("<script>", { id: "paging-header-tpl", type: "text/template" }).text(pagingHeaderTpl));
                appendSetFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTpl));
                spyOn(pagingView, 'showPagingError').andCallFake(function() { });
                requests = create_sinon.requests(this);
            });

            it('can set the current page', function () {
                pagingView.setPage(0);
                respondWithMockAssets(requests);
                expect(pagingView.collection.currentPage).toBe(0);
                pagingView.setPage(1);
                respondWithMockAssets(requests);
                expect(pagingView.collection.currentPage).toBe(1);
            });

            it('should not change page after a server error', function () {
                pagingView.setPage(0);
                respondWithMockAssets(requests);
                pagingView.setPage(1);
                requests[1].respond(500);
                expect(pagingView.collection.currentPage).toBe(0);
            });

            it('does not move forward after a server error', function () {
                pagingView.setPage(0);
                respondWithMockAssets(requests);
                pagingView.nextPage();
                requests[1].respond(500);
                expect(pagingView.collection.currentPage).toBe(0);
            });

            it('can move to the next page', function () {
                pagingView.setPage(0);
                respondWithMockAssets(requests);
                pagingView.nextPage();
                respondWithMockAssets(requests);
                expect(pagingView.collection.currentPage).toBe(1);
            });

            it('can not move forward from the final page', function () {
                pagingView.setPage(1);
                respondWithMockAssets(requests);
                pagingView.nextPage();
                expect(requests.length).toBe(1);
            });

            it('can move back a page', function () {
                pagingView.setPage(1);
                respondWithMockAssets(requests);
                pagingView.previousPage();
                respondWithMockAssets(requests);
                expect(pagingView.collection.currentPage).toBe(0);
            });

            it('can not move back from the first page', function () {
                pagingView.setPage(0);
                respondWithMockAssets(requests);
                pagingView.previousPage();
                expect(requests.length).toBe(1);
            });

            it('does not move back after a server error', function () {
                pagingView.setPage(1);
                respondWithMockAssets(requests);
                pagingView.previousPage();
                requests[1].respond(500);
                expect(pagingView.collection.currentPage).toBe(1);
            });
        });

        describe("PagingHeader", function () {
            var pagingHeader,
                pagingView;

            beforeEach(function () {
                setFixtures($("<script>", { id: "paging-header-tpl", type: "text/template" }).text(pagingHeaderTpl));
                appendSetFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTpl));
                var assets = new AssetCollection();
                assets.url = "assets_url";
                pagingView = new MockPagingView({collection: assets});
                pagingHeader = new PagingHeader({view: pagingView});
                spyOn(pagingView, 'showPagingError').andCallFake(function() { });
            });

            describe("Next page button", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);

                    // Render the page and header so that they can react to events
                    pagingView.render();
                    pagingHeader.render();

                    // Start on the first page
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                });

                it('does not move forward if a server error occurs', function () {
                    // Verify that 500 errors don't cause the page to move
                    pagingHeader.$('.next-page-link').click();
                    requests[1].respond(500);
                    expect(pagingView.collection.currentPage).toBe(0);
                });

                it('can move to the next page', function () {
                    pagingHeader.$('.next-page-link').click();
                    respondWithMockAssets(requests);
                    expect(pagingView.collection.currentPage).toBe(1);
                });

                it('should be enabled when there is at least one more page', function () {
                    expect(pagingHeader.$('.next-page-link')).not.toHaveClass('is-disabled');
                });

                it('should be disabled on the final page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.next-page-link')).toHaveClass('is-disabled');
                });


                it('should be disabled on an empty page', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingHeader.$('.next-page-link')).toHaveClass('is-disabled');
                });
            });

            describe("Previous page button", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);

                    // Render the page and header so that they can react to events
                    pagingView.render();
                    pagingHeader.render();

                    // Start on the second page
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                });

                it('does not move back if a server error occurs', function () {
                    pagingHeader.$('.previous-page-link').click();
                    requests[1].respond(500);
                    expect(pagingView.collection.currentPage).toBe(1);
                });

                it('can go back a page', function () {
                    pagingHeader.$('.previous-page-link').click();
                    respondWithMockAssets(requests);
                    expect(pagingView.collection.currentPage).toBe(0);
                });

                it('should be disabled on the first page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.previous-page-link')).toHaveClass('is-disabled');
                });

                it('should be enabled on the second page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.previous-page-link')).not.toHaveClass('is-disabled');
                });

                it('should be disabled for an empty page', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingHeader.$('.previous-page-link')).toHaveClass('is-disabled');
                });
            });

            describe("Asset count label", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);
                });

                it('should show correct count on first page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.count-current-shown')).toHaveHtml('1-3');
                });

                it('should show correct count on second page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.count-current-shown')).toHaveHtml('4-4');
                });

                it('should show correct count for an empty collection', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingHeader.$('.count-current-shown')).toHaveHtml('0-0');
                });
            });

            describe("Asset total label", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);
                });

                it('should show correct total on the first page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.count-total')).toHaveText('4 total');
                });

                it('should show correct total on the second page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingHeader.$('.count-total')).toHaveText('4 total');
                });

                it('should show zero total for an empty collection', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingHeader.$('.count-total')).toHaveText('0 total');
                });
            });
        });

        describe("PagingFooter", function () {
            var pagingFooter,
                pagingView;

            beforeEach(function () {
                setFixtures($("<script>", { id: "paging-footer-tpl", type: "text/template" }).text(pagingFooterTpl));
                appendSetFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTpl));
                var assets = new AssetCollection();
                assets.url = "assets_url";
                pagingView = new MockPagingView({collection: assets});
                pagingFooter = new PagingFooter({view: pagingView});
                spyOn(pagingView, 'showPagingError').andCallFake(function() { });
            });

            describe("Next page button", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);

                    // Render the page and header so that they can react to events
                    pagingView.render();
                    pagingFooter.render();

                    // Start on the first page
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                });

                it('does not move forward if a server error occurs', function () {
                    pagingFooter.$('.next-page-link').click();
                    requests[1].respond(500);
                    expect(pagingView.collection.currentPage).toBe(0);
                });

                it('can move to the next page', function () {
                    pagingFooter.$('.next-page-link').click();
                    respondWithMockAssets(requests);
                    expect(pagingView.collection.currentPage).toBe(1);
                });

                it('should be enabled when there is at least one more page', function () {
                    expect(pagingFooter.$('.next-page-link')).not.toHaveClass('is-disabled');
                });

                it('should be disabled on the final page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingFooter.$('.next-page-link')).toHaveClass('is-disabled');
                });

                it('should be disabled on an empty page', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingFooter.$('.next-page-link')).toHaveClass('is-disabled');
                });
            });

            describe("Previous page button", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);

                    // Render the page and header so that they can react to events
                    pagingView.render();
                    pagingFooter.render();

                    // Start on the second page
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);

                });

                it('does not move back if a server error occurs', function () {
                    // Verify that 500 errors don't cause the page to move
                    pagingFooter.$('.previous-page-link').click();
                    requests[1].respond(500);
                    expect(pagingView.collection.currentPage).toBe(1);
                });

                it('can go back a page', function () {
                    pagingFooter.$('.previous-page-link').click();
                    respondWithMockAssets(requests);
                    expect(pagingView.collection.currentPage).toBe(0);
                });

                it('should be disabled on the first page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingFooter.$('.previous-page-link')).toHaveClass('is-disabled');
                });

                it('should be enabled on the second page', function () {
                    expect(pagingFooter.$('.previous-page-link')).not.toHaveClass('is-disabled');
                });

                it('should be disabled for an empty page', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingFooter.$('.previous-page-link')).toHaveClass('is-disabled');
                });
            });

            describe("Page total label", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);
                });

                it('should show 1 on the first page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingFooter.$('.current-page')).toHaveText('1');
                });

                it('should show 2 on the second page', function () {
                    pagingView.setPage(1);
                    respondWithMockAssets(requests);
                    expect(pagingFooter.$('.current-page')).toHaveText('2');
                });

                it('should show 1 for an empty collection', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingFooter.$('.current-page')).toHaveText('1');
                });
            });

            describe("Page total label", function () {
                var requests;

                beforeEach(function () {
                    requests = create_sinon.requests(this);
                });

                it('should show the correct value with more than one page', function () {
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                    expect(pagingFooter.$('.total-pages')).toHaveText('2');
                });

                it('should show page 1 when there are no assets', function () {
                    pagingView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyPage);
                    expect(pagingFooter.$('.total-pages')).toHaveText('1');
                });
            });

            describe("Page input field", function () {
                var requests,
                    input;

                beforeEach(function () {
                    requests = create_sinon.requests(this);
                    input = pagingFooter.$('.page-number-input').first();
                    pagingFooter.render();
                    pagingView.setPage(0);
                    respondWithMockAssets(requests);
                });

                it('should initially have a blank page input', function () {
                    expect(pagingFooter.$('.page-number-input')).toHaveValue('');
                });

                it('should handle invalid page requests', function () {
                    pagingFooter.$('.page-number-input').val('abc');
                    pagingFooter.$('.page-number-input').trigger('change');
                    expect(pagingView.collection.currentPage).toBe(0);
                    expect(pagingFooter.$('.page-number-input')).toHaveValue('');
                });

                it('should switch pages via the input field', function () {
                    pagingFooter.$('.page-number-input').val('2');
                    pagingFooter.$('.page-number-input').trigger('change');
                    create_sinon.respondWithJson(requests, mockSecondPage);
                    expect(pagingView.collection.currentPage).toBe(1);
                    expect(pagingFooter.$('.page-number-input')).toHaveValue('');
                });

                it('should handle AJAX failures when switching pages via the input field', function () {
                    pagingFooter.$('.page-number-input').val('2');
                    pagingFooter.$('.page-number-input').trigger('change');
                    requests[1].respond(500);
                    expect(pagingView.collection.currentPage).toBe(0);
                    expect(pagingFooter.$('.page-number-input')).toHaveValue('');
                });
            });
        });
    });
