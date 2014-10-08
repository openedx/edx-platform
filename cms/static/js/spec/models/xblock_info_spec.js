define(['backbone', 'js/models/xblock_info'],
    function(Backbone, XBlockInfo) {
        describe('XblockInfo isEditableOnCourseOutline', function() {
            it('works correct', function() {
                expect(new XBlockInfo({'category': 'chapter'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'course'}).isEditableOnCourseOutline()).toBe(false);
                expect(new XBlockInfo({'category': 'sequential'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'vertical'}).isEditableOnCourseOutline()).toBe(true);
            });
        });
    }
);
