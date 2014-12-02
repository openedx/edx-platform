define([ "jquery", "js/common_helpers/ajax_helpers", "js/views/asset", "js/views/assets",
    "js/models/asset", "js/collections/asset", "js/spec_helpers/view_helpers" ],
    function ($, AjaxHelpers, AssetView, AssetsView, AssetModel, AssetCollection, ViewHelpers) {

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

            mockExampleAssetsResponse = {
              sort: "uploadDate",
              end: 50,
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
                  "display_name": "STRAT_L5_PositionalProprietary_PrivelegedAssets.png",
                  "url": "/c4x/A/CS102/asset/STRAT_L5_PositionalProprietary_PrivelegedAssets.png",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_L5_PositionalProprietary_PrivelegedAssets.png",
                  "portable_url": "/static/STRAT_L5_PositionalProprietary_PrivelegedAssets.png",
                  "thumbnail": "/c4x/A/CS102/thumbnail/STRAT_L5_PositionalProprietary_PrivelegedAssets.jpg",
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_L5_PositionalProprietary_PrivelegedAssets.png"
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
                },
                {
                  "display_name": "A fresh look at strategy under uncertainty - an interview.pdf",
                  "url": "/c4x/A/CS102/asset/A_fresh_look_at_strategy_under_uncertainty_-_an_interview.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/A_fresh_look_at_strategy_under_uncertainty_-_an_interview.pdf",
                  "portable_url": "/static/A_fresh_look_at_strategy_under_uncertainty_-_an_interview.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/A_fresh_look_at_strategy_under_uncertainty_-_an_interview.pdf"
                },
                {
                  "display_name": "STRAT_02-02-v2f.pdf",
                  "url": "/c4x/A/CS102/asset/STRAT_02-02-v2f.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_02-02-v2f.pdf",
                  "portable_url": "/static/STRAT_02-02-v2f.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_02-02-v2f.pdf"
                },
                {
                  "display_name": "STRAT_02-09-v2e.pdf",
                  "url": "/c4x/A/CS102/asset/STRAT_02-09-v2e.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_02-09-v2e.pdf",
                  "portable_url": "/static/STRAT_02-09-v2e.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_02-09-v2e.pdf"
                },
                {
                  "display_name": "Delegation worksheet.pdf",
                  "url": "/c4x/A/CS102/asset/Delegation_worksheet.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/Delegation_worksheet.pdf",
                  "portable_url": "/static/Delegation_worksheet.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/Delegation_worksheet.pdf"
                },
                {
                  "display_name": "STRAT_04-08_v2e.pdf",
                  "url": "/c4x/A/CS102/asset/STRAT_04-08_v2e.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_04-08_v2e.pdf",
                  "portable_url": "/static/STRAT_04-08_v2e.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_04-08_v2e.pdf"
                },
                {
                  "display_name": "STRAT_05-13_v2d.pdf",
                  "url": "/c4x/A/CS102/asset/STRAT_05-13_v2d.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_05-13_v2d.pdf",
                  "portable_url": "/static/STRAT_05-13_v2d.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_05-13_v2d.pdf"
                },
                {
                  "display_name": "STRAT_06-09-v2f.pdf",
                  "url": "/c4x/A/CS102/asset/STRAT_06-09-v2f.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/STRAT_06-09-v2f.pdf",
                  "portable_url": "/static/STRAT_06-09-v2f.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/STRAT_06-09-v2f.pdf"
                },
                {
                  "display_name": "Strategy's strategist - An interview with Richard Rumelt.pdf",
                  "url": "/c4x/A/CS102/asset/Strategy_s_strategist_-_An_interview_with_Richard_Rumelt.pdf",
                  "date_added": "Oct 20, 2014 at 11:00 UTC",
                  "id": "/c4x/A/CS102/asset/Strategy_s_strategist_-_An_interview_with_Richard_Rumelt.pdf",
                  "portable_url": "/static/Strategy_s_strategist_-_An_interview_with_Richard_Rumelt.pdf",
                  "thumbnail": null,
                  "locked": false,
                  "external_url": "localhost:8000/c4x/A/CS102/asset/Strategy_s_strategist_-_An_interview_with_Richard_Rumelt.pdf"
                }
              ],
              pageSize: 50,
              totalCount: 172,
              start: 0,
              page: 0
            }

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
                setup = function(responseData) {
                    var requests;
                    requests = AjaxHelpers.requests(this);
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
                it('shows type select menu, selects type, and filters results', function () {
                    expect(assetsView).toBeDefined();
                    setup.call(this, mockExampleAssetsResponse);

                    $typeColumn = $('.type-col.filterable-column .nav-dd');
                    expect($typeColumn.length).toBe(1);
                    $typeColumn.click();
                    expect($typeColumn.find('.wrapper-nav-sub')).toHaveClass('is-shown');
                    expect($typeColumn.find('h3.title')).toHaveClass('is-selected');

                    var assetsNumber = $('#asset-table-body .type-col').length;
                });
            });
        });
    });
