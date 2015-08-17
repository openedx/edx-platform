define(['jquery', 'underscore', 'js/views/edit_chapter', 'js/models/course'],
    function ($, _, EditChapter, Course) {
    'use strict';

        describe('EditChapter', function () {

                beforeEach(function() {
                    window.course = new Course({
                        id: '1',
                        name: '&amp;lt;Vedran&#39;s course&amp;gt;',
                        url_name: 'course_name',
                        org: 'course_org',
                        num: 'course_num',
                        revision: 'course_rev'
                    });
                });

            describe('openUploadDialog', function() {

                it('displays the encoded name of the course', function () {
                    var title = _.template(('Upload a new PDF to "<%= name %>"'),
                        {name: course.get('name')});
                    expect(title).toBe('Upload a new PDF to "&amp;lt;Vedran&#39;s course&amp;gt;"');
                });
            });
        });
});