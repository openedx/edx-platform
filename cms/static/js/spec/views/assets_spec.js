define([ "jquery", "js/common_helpers/ajax_helpers", "URI", "js/views/asset", "js/views/assets",
    "js/models/asset", "js/collections/asset", "js/spec_helpers/view_helpers"],
    function ($, AjaxHelpers, URI, AssetView, AssetsView, AssetModel, AssetCollection, ViewHelpers) {

        describe("Assets", function() {
            var assetsView, mockEmptyAssetsResponse, mockAssetUploadResponse, mockFileUpload,
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

                spyOn($.fn, "fileupload").andReturn("");

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

            var mockExampleAssetsResponse = {
                sort: "uploadDate",
                end: 2,
                assets: [
                    {
                        "display_name": "pivo.jpg",
                        "url": "/c4x/A/CS102/asset/pivo.jpg",
                        "date_added": "Nov 07, 2014 at 17:47 UTC",
                        "id": "/c4x/A/CS102/asset/pivo.jpg",
                        "portable_url": "/static/pivo.jpg",
                        "thumbnail": "/c4x/A/CS102/thumbnail/pivo.jpg",
                        "locked": false,
                        "external_url": "localhost:8000/c4x/A/CS102/asset/pivo.jpg"
                    },
                    {
                        "display_name": "STRAT_02-06-v2f.pdf",
                        "url": "/c4x/A/CS102/asset/STRAT_02-06-v2f.pdf",
                        "date_added": "Oct 20, 2014 at 11:00 UTC",
                        "id": "/c4x/A/CS102/asset/STRAT_02-06-v2f.pdf",
                        "portable_url": "/static/STRAT_02-06-v2f.pdf",
                        "thumbnail": null,
                        "locked": false,
                        "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_02-06-v2f.pdf"
                    }
                ],
                pageSize: 2,
                totalCount: 2,
                start: 0,
                page: 0
            };

            var mockExampleFilteredAssetsResponse = {
                sort: "uploadDate",
                end: 1,
                assets: [
                    {
                        "display_name": "pivo.jpg",
                        "url": "/c4x/A/CS102/asset/pivo.jpg",
                        "date_added": "Nov 07, 2014 at 17:47 UTC",
                        "id": "/c4x/A/CS102/asset/pivo.jpg",
                        "portable_url": "/static/pivo.jpg",
                        "thumbnail": "/c4x/A/CS102/thumbnail/pivo.jpg",
                        "locked": false,
                        "external_url": "localhost:8000/c4x/A/CS102/asset/pivo.jpg"
                    }
                ],
                pageSize: 1,
                totalCount: 1,
                start: 0,
                page: 0
            };

            mockAssetUploadResponse = {
                asset: mockAsset,
                msg: "Upload completed"
            };

            mockFileUpload = {
                files: [{name: 'largefile', size: 0}]
            };

            var respondWithMockAssets = function(requests) {
                var requestIndex = requests.length - 1;
                var request = requests[requestIndex];
                var url = new URI(request.url);
                var queryParameters = url.query(true); // Returns an object with each query parameter stored as a value
                var asset_type = queryParameters.asset_type;
                var response = asset_type !== '' ? mockExampleFilteredAssetsResponse : mockExampleAssetsResponse;
                AjaxHelpers.respondWithJson(requests, response, requestIndex);
            };

            $.fn.fileupload = function() {
                return '';
            };

            var event = {};
            event.target = {"value": "dummy.jpg"};

            describe("AssetsView", function () {
                var setup;
                setup = function(responseData) {
                    var requests = AjaxHelpers.requests(this);
                    assetsView.setPage(0);
                    if (!responseData){
                        AjaxHelpers.respondWithJson(requests, mockEmptyAssetsResponse);
                    }
                    else{
                        AjaxHelpers.respondWithJson(requests, responseData);
                    }
                    return requests;
                };

                beforeEach(function () {
                    ViewHelpers.installMockAnalytics();
                });

                afterEach(function () {
                    ViewHelpers.removeMockAnalytics();
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

                it('has properly initialized constants for handling upload file errors', function() {
                    expect(assetsView).toBeDefined();
                    expect(assetsView.uploadChunkSizeInMBs).toBeDefined();
                    expect(assetsView.maxFileSizeInMBs).toBeDefined();
                    expect(assetsView.uploadChunkSizeInBytes).toBeDefined();
                    expect(assetsView.maxFileSizeInBytes).toBeDefined();
                    expect(assetsView.largeFileErrorMsg).toBeNull();
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

                it('blocks file uploads larger than the max file size', function() {
                    expect(assetsView).toBeDefined();

                    mockFileUpload.files[0].size = assetsView.maxFileSize * 10;

                    $('.choose-file-button').click();
                    $(".upload-modal .file-chooser").fileupload('add', mockFileUpload);
                    expect($('.upload-modal h1').text()).not.toContain("Uploading");

                    expect(assetsView.largeFileErrorMsg).toBeDefined();
                    expect($('div.progress-bar').text()).not.toContain("Upload completed");
                    expect($('div.progress-fill').width()).toBe(0);
                });

                it('allows file uploads equal in size to the max file size', function() {
                    expect(assetsView).toBeDefined();

                    mockFileUpload.files[0].size = assetsView.maxFileSize;

                    $('.choose-file-button').click();
                    $(".upload-modal .file-chooser").fileupload('add', mockFileUpload);

                    expect(assetsView.largeFileErrorMsg).toBeNull();
                });

                it('allows file uploads smaller than the max file size', function() {
                    expect(assetsView).toBeDefined();

                    mockFileUpload.files[0].size = assetsView.maxFileSize / 100;

                    $('.choose-file-button').click();
                    $(".upload-modal .file-chooser").fileupload('add', mockFileUpload);

                    expect(assetsView.largeFileErrorMsg).toBeNull();
                });

                it('make sure _toggleFilterColumn filters asset list', function () {
                    expect(assetsView).toBeDefined();
                    var requests = AjaxHelpers.requests(this);
                    $.each(assetsView.filterableColumns, function(columnID, columnData){
                        var $typeColumn = $('#' + columnID);
                        assetsView.setPage(0);
                        respondWithMockAssets(requests);
                        var assetsNumber = assetsView.collection.length;
                        assetsView._toggleFilterColumn('Images');
                        respondWithMockAssets(requests);
                        var assetsNumberFiltered = assetsView.collection.length;
                        expect(assetsNumberFiltered).toBeLessThan(assetsNumber);
                        expect($typeColumn.find('.title .type-filter')).not.toEqual(assetsView.allLabel);
                    });
                });

                it('opens and closes select type menu', function () {
                    expect(assetsView).toBeDefined();
                    setup.call(this, mockExampleAssetsResponse);
                    $.each(assetsView.filterableColumns, function(columnID, columnData){
                        var $typeColumn = $('#' + columnID);
                        expect($typeColumn).toBeVisible();
                        var assetsNumber = $('#asset-table-body .type-col').length;
                        assetsView.openFilterColumn($typeColumn);
                        expect($typeColumn.find('.wrapper-nav-sub')).toHaveClass('is-shown');
                        expect($typeColumn.find('.title')).toHaveClass('is-selected');
                        expect($typeColumn.find('.column-filter-link')).toBeVisible();
                        $typeColumn.find('.wrapper-nav-sub').trigger('click');
                        expect($typeColumn.find('.wrapper-nav-sub').hasClass('is-shown')).toBe(false);
                    });
                });

                it('shows type select menu, selects type, and filters results', function () {
                    expect(assetsView).toBeDefined();
                    var requests = AjaxHelpers.requests(this);
                    $.each(assetsView.filterableColumns, function(columnID, columnData){
                        assetsView.setPage(0);
                        respondWithMockAssets(requests);
                        var $typeColumn = $('#' + columnID);
                        expect($typeColumn).toBeVisible();
                        var assetsNumber = assetsView.collection.length;
                        $typeColumn.trigger('click');
                        expect($typeColumn.find('.wrapper-nav-sub')).toHaveClass('is-shown');
                        expect($typeColumn.find('.title')).toHaveClass('is-selected');
                        var $firstFilter = $($typeColumn.find('li.nav-item a')[1]);
                        $firstFilter.trigger('click');
                        respondWithMockAssets(requests);
                        var assetsNumberFiltered = assetsView.collection.length;
                        expect(assetsNumberFiltered).toBeLessThan(assetsNumber);
                    });
                });
            });
        });
    });
