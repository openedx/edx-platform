define(['backbone', 'js/models/xblock_info'],
    function(Backbone, XBlockInfo) {
        describe('XblockInfo isEditableOnCourseOutline', function() {
            it('works correct', function() {
                expect(new XBlockInfo({'category': 'chapter'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'course'}).isEditableOnCourseOutline()).toBe(false);
                expect(new XBlockInfo({'category': 'sequential'}).isEditableOnCourseOutline()).toBe(true);
                expect(new XBlockInfo({'category': 'vertical'}).isEditableOnCourseOutline()).toBe(true);
            });

            it('section content should be hidden for an entrance exam e.g. trash icon, drag', function(){
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {'is_entrance_exam_section':true}})
                    .showSectionContent()).toBe(false);
            });

            it('entrance exam score should be retrieved', function(){
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {'is_entrance_exam_section':true, 'exam_min_score':50}})
                    .getExamScore()).toBe(50);
            });

            it('subsection content should be hidden for an entrance exam e.g. trash icon, drag, settings ', function(){
                expect(new XBlockInfo({'category': 'sequential', 'override_type': {'is_entrance_exam_subsection':true}})
                    .showSubSectionContent()).toBe(false);
            });

            it('subsection content should not be hidden other then entrance exam e.g. trash icon, drag, settings ', function(){
                expect(new XBlockInfo({'category': 'sequential', 'override_type': {'is_entrance_exam_subsection':false}})
                    .showSubSectionContent()).toBe(true);
            });

            it('section content should not be hidden other then entrance exam', function(){
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {'is_entrance_exam_section':false}}).showSectionContent()).toBe(true);
                expect(new XBlockInfo({'category': 'chapter', 'override_type': {}}).showSectionContent()).toBe(true);
            });
        });
    }
);
