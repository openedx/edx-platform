define(['backbone', 'js/models/xblock_info'],
    function(Backbone, XBlockInfo) {
        describe('XblockInfo isEditableOnCourseOutline', function() {
            it('works correct', function() {
                expect(new XBlockInfo({'category': 'chapter'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'course'}).isEditableOnCourseOutline()).toBe(false);
                expect(new XBlockInfo({'category': 'sequential'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'vertical'}).isEditableOnCourseOutline()).toBe(true);
            });

            it('cannot delete an entrance exam', function(){
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {'is_entrance_exam':true}})
                    .canBeDeleted()).toBe(false);
            });

            it('can delete module rather then entrance exam', function(){
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {'is_entrance_exam':false}}).canBeDeleted()).toBe(true);
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {}}).canBeDeleted()).toBe(true);
            });
        });
    }
);
