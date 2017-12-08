define(['backbone', 'js/models/xblock_info'],
    function(Backbone, XBlockInfo) {
        describe('XblockInfo isEditableOnCourseOutline', function() {
            it('works correct', function() {
                expect(new XBlockInfo({category: 'chapter'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({category: 'course'}).isEditableOnCourseOutline()).toBe(false);
                expect(new XBlockInfo({category: 'sequential'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({category: 'vertical'}).isEditableOnCourseOutline()).toBe(true);
            });
        });

        describe('XblockInfo actions state and header visibility ', function() {
            it('works correct to hide icons e.g. trash icon, drag when actions are not required', function() {
                expect(new XBlockInfo({category: 'chapter', actions: {deletable: false}})
                    .isDeletable()).toBe(false);
                expect(new XBlockInfo({category: 'chapter', actions: {draggable: false}})
                    .isDraggable()).toBe(false);
                expect(new XBlockInfo({category: 'chapter', actions: {childAddable: false}})
                    .isChildAddable()).toBe(false);
            });

            it('works correct to show icons e.g. trash icon, drag when actions are required', function() {
                expect(new XBlockInfo({category: 'chapter', actions: {deletable: true}})
                    .isDeletable()).toBe(true);
                expect(new XBlockInfo({category: 'chapter', actions: {draggable: true}})
                    .isDraggable()).toBe(true);
                expect(new XBlockInfo({category: 'chapter', actions: {childAddable: true}})
                    .isChildAddable()).toBe(true);
            });

            it('displays icons e.g. trash icon, drag when actions are undefined', function() {
                expect(new XBlockInfo({category: 'chapter', actions: {}})
                    .isDeletable()).toBe(true);
                expect(new XBlockInfo({category: 'chapter', actions: {}})
                    .isDraggable()).toBe(true);
                expect(new XBlockInfo({category: 'chapter', actions: {}})
                    .isChildAddable()).toBe(true);
            });

            it('works correct to hide header content', function() {
                expect(new XBlockInfo({category: 'sequential', is_header_visible: false})
                    .isHeaderVisible()).toBe(false);
            });

            it('works correct to show header content when is_header_visible is not defined', function() {
                expect(new XBlockInfo({category: 'sequential', actions: {deletable: true}})
                    .isHeaderVisible()).toBe(true);
            });
        });
    }
);
