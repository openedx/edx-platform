define(['jquery', 'URI', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'common/js/components/utils/view_utils',
        'js/views/xblock', 'js/models/xblock_info', 'xmodule', 'cms/js/main', 'xblock/cms.runtime.v1'],
    function($, URI, AjaxHelpers, ViewUtils, XBlockView, XBlockInfo) {
        'use strict';
        describe('XBlockView', function() {
            var model, xblockView, mockXBlockHtml;

            beforeEach(function() {
                model = new XBlockInfo({
                    id: 'testCourse/branch/draft/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
                xblockView = new XBlockView({
                    model: model
                });
            });

            mockXBlockHtml = readFixtures('mock/mock-xblock.underscore');

            it('can render a nested xblock', function() {
                var requests = AjaxHelpers.requests(this);
                xblockView.render();
                AjaxHelpers.respondWithJson(requests, {
                    html: mockXBlockHtml,
                    resources: []
                });

                expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
            });
        });
    });
