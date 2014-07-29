define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/views/utils/view_utils",
        "js/views/unit_outline", "js/models/xblock_info"],
    function ($, create_sinon, view_helpers, ViewUtils, UnitOutlineView, XBlockInfo) {

        describe("UnitOutlineView", function() {
            var createUnitOutlineView, createMockXBlockInfo,
                requests, model, unitOutlineView;

            createUnitOutlineView = function(test, unitJSON, createOnly) {
                requests = create_sinon.requests(test);
                model = new XBlockInfo(unitJSON, { parse: true });
                unitOutlineView = new UnitOutlineView({
                    model: model,
                    el: $('.wrapper-unit-overview')
                });
                if (!createOnly) {
                    unitOutlineView.render();
                }
                return unitOutlineView;
            };

            createMockXBlockInfo = function(displayName) {
                return {
                    id: 'mock-unit',
                    category: 'vertical',
                    display_name: displayName,
                    studio_url: '/container/mock-unit',
                    visibility_state: 'unscheduled',
                    ancestor_info: {
                        ancestors: [{
                            id: 'mock-subsection',
                            category: 'sequential',
                            display_name: 'Mock Subsection',
                            studio_url: '/course/mock-course?show=mock-subsection',
                            visibility_state: 'unscheduled',
                            child_info: {
                                category: 'vertical',
                                display_name: 'Unit',
                                children: [{
                                    id: 'mock-unit',
                                    category: 'vertical',
                                    display_name: displayName,
                                    studio_url: '/container/mock-unit',
                                    visibility_state: 'unscheduled'
                                }, {
                                    id: 'mock-unit-2',
                                    category: 'vertical',
                                    display_name: 'Mock Unit 2',
                                    studio_url: '/container/mock-unit-2',
                                    visibility_state: 'unscheduled'
                                }]
                            }
                        }, {
                            id: 'mock-section',
                            category: 'chapter',
                            display_name: 'Section',
                            studio_url: '/course/slashes:mock-course?show=mock-section',
                            visibility_state: 'unscheduled'
                        }, {
                            id: 'mock-course',
                            category: 'course',
                            display_name: 'Mock Course',
                            studio_url: '/course/mock-course',
                            visibility_state: 'unscheduled'
                        }]
                    },
                    metadata: {
                        display_name: 'Mock Unit'
                    }
                };
            };

            beforeEach(function () {
                view_helpers.installMockAnalytics();
                view_helpers.installViewTemplates();
                view_helpers.installTemplate('unit-outline');
                appendSetFixtures('<div class="wrapper-unit-overview"></div>');
            });

            afterEach(function () {
                view_helpers.removeMockAnalytics();
            });

            it('can render itself', function() {
                createUnitOutlineView(this, createMockXBlockInfo('Mock Unit'));
                expect(unitOutlineView.$('.list-sections')).toExist();
                expect(unitOutlineView.$('.list-subsections')).toExist();
                expect(unitOutlineView.$('.list-units')).toExist();
            });

            it('can add a unit', function() {
                var redirectSpy;
                createUnitOutlineView(this, createMockXBlockInfo('Mock Unit'));
                redirectSpy = spyOn(ViewUtils, 'redirect');
                unitOutlineView.$('.outline-subsection > .outline-content  > .add-unit .button-new').click();
                create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                    category: 'vertical',
                    display_name: 'Unit',
                    parent_locator: 'mock-subsection'
                });
                create_sinon.respondWithJson(requests, {
                    locator: "new-mock-unit",
                    courseKey: "slashes:MockCourse"
                });
                expect(redirectSpy).toHaveBeenCalledWith('/container/new-mock-unit?action=new');
            });

            it('refreshes when the XBlockInfo model syncs', function() {
                var updatedDisplayName = 'Mock Unit Updated', unitHeader;
                createUnitOutlineView(this, createMockXBlockInfo('Mock Unit'));
                unitOutlineView.refresh();
                create_sinon.expectJsonRequest(requests, 'GET', '/xblock/mock-unit');
                create_sinon.respondWithJson(requests,
                    createMockXBlockInfo(updatedDisplayName));
                expect(unitOutlineView.$('.outline-unit .unit-title').first().text().trim()).toBe(updatedDisplayName);
            });
        });
    });
