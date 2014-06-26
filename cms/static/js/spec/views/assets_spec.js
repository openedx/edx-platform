define([ "jquery", "js/spec_helpers/create_sinon", "js/views/asset", "js/views/assets",
    "js/models/asset", "js/collections/asset", "js/spec_helpers/view_helpers" ],
    function ($, create_sinon, AssetView, AssetsView, AssetModel, AssetCollection, view_helpers) {

        describe("Assets", function() {
            var assetsView, mockEmptyAssetsResponse, mockAssetUploadResponse,
                assetLibraryTpl, assetTpl, pagingFooterTpl, pagingHeaderTpl, uploadModalTpl;

            assetLibraryTpl = readFixtures('asset-library.underscore');
            assetTpl = readFixtures('asset.underscore');
            pagingHeaderTpl = readFixtures('paging-header.underscore');
            pagingFooterTpl = readFixtures('paging-footer.underscore');
            uploadModalTpl = readFixtures('asset-upload-modal.underscore');

            beforeEach(function () {
                setFixtures($("<script>", { id: "asset-library-tpl", type: "text/template" }).text(assetLibraryTpl));
                appendSetFixtures($("<script>", { id: "asset-tpl", type: "text/template" }).text(assetTpl));
                appendSetFixtures($("<script>", { id: "paging-header-tpl", type: "text/template" }).text(pagingHeaderTpl));
                appendSetFixtures($("<script>", { id: "paging-footer-tpl", type: "text/template" }).text(pagingFooterTpl));
                appendSetFixtures(uploadModalTpl);
                appendSetFixtures(sandbox({ id: "asset_table_body" }));

                var collection = new AssetCollection();
                collection.url = "assets-url";
                assetsView = new AssetsView({
                    collection: collection,
                    el: $('#asset_table_body')
                });
                assetsView.render();
            });

            var mockAsset = {
                display_name: "dummy.jpg",
                url: 'actual_asset_url',
                portable_url: 'portable_url',
                date_added: 'date',
                thumbnail: null,
                locked: false,
                id: 'id_1'
            };

            mockEmptyAssetsResponse = {
                assets: [],
                start: 0,
                end: 0,
                page: 0,
                pageSize: 5,
                totalCount: 0
            };

            mockAssetUploadResponse = {
                asset: mockAsset,
                msg: "Upload completed"
            };

            $.fn.fileupload = function() {
                return '';
            };

            var event = {}
            event.target = {"value": "dummy.jpg"};

            describe("AssetsView", function () {
                var setup;
                setup = function() {
                    var requests;
                    requests = create_sinon.requests(this);
                    assetsView.setPage(0);
                    create_sinon.respondWithJson(requests, mockEmptyAssetsResponse);
                    return requests;
                };

                beforeEach(function () {
                    view_helpers.installMockAnalytics();
                });

                afterEach(function () {
                    view_helpers.removeMockAnalytics();
                });

                it('shows the upload modal when clicked on "Upload your first asset" button', function () {
                    expect(assetsView).toBeDefined();
                    appendSetFixtures('<div class="ui-loading"/>');
                    expect($('.ui-loading').is(':visible')).toBe(true);
                    expect($('.upload-button').is(':visible')).toBe(false);
                    setup.call(this);
                    expect($('.ui-loading').is(':visible')).toBe(false);
                    expect($('.upload-button').is(':visible')).toBe(true);

                    expect($('.upload-modal').is(':visible')).toBe(false);
                    $('a:contains("Upload your first asset")').click();
                    expect($('.upload-modal').is(':visible')).toBe(true);

                    $('.close-button').click();
                    expect($('.upload-modal').is(':visible')).toBe(false);
                });

                it('uploads file properly', function () {
                    var requests = setup.call(this);
                    expect(assetsView).toBeDefined();
                    spyOn(assetsView, "addAsset").andCallFake(function () {
                        assetsView.collection.add(mockAssetUploadResponse.asset);
                        assetsView.renderPageItems();
                        assetsView.setPage(0);
                    });

                    $('a:contains("Upload your first asset")').click();
                    expect($('.upload-modal').is(':visible')).toBe(true);

                    $('.choose-file-button').click();
                    $("input[type=file]").change();
                    expect($('.upload-modal h1').text()).toContain("Uploading");

                    assetsView.showUploadFeedback(event, 100);
                    expect($('div.progress-bar').text()).toContain("100%");

                    assetsView.displayFinishedUpload(mockAssetUploadResponse);
                    expect($('div.progress-bar').text()).toContain("Upload completed");
                    $('.close-button').click();
                    expect($('.upload-modal').is(':visible')).toBe(false);

                    expect($('#asset_table_body').html()).toContain("dummy.jpg");
                    expect(assetsView.collection.length).toBe(1);
                });
            });
        });
    });
