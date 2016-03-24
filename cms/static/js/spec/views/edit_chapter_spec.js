define(['jquery', 'underscore', 'js/views/edit_chapter', 'js/models/course', 'js/collections/chapter', 'js/models/chapter', "js/spec_helpers/modal_helpers"],
    function ($, _, EditChapter, Course, ChapterCollection, ChapterModel, ModelHelpers) {
    'use strict';
    describe('EditChapter', function () {

        describe('openUploadDialog', function() {
            var edit_chapter_fixture = readFixtures('edit-chapter.underscore');

            beforeEach(function() {
                var course = new Course({
                    name: '&amp;lt;Vedran&#39;s course&amp;gt;',
                });
                this.model = new ChapterModel({name: 'test-model'});
                this.collection = new ChapterCollection(this.model);
            });
            it('displays the encoded name of the course', function () {
                setFixtures(edit_chapter_fixture);
                var test = new EditChapter({model: this.model});
                $('.action-upload').click();
                expect($('#modal-window-title').text()).toBe(2);
            });
        });
    });
});