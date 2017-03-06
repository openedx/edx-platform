define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/discovery/models/course_card',
    'js/discovery/views/course_card'
], function($, TemplateHelpers, CourseCard, CourseCardView) {
    'use strict';


    var JSON_RESPONSE = {
        "total": 365,
        "results": [
            {
                "data": {
                    "modes": [
                        "honor"
                    ],
                    "course": "edX/DemoX/Demo_Course",
                    "enrollment_start": "2015-04-21T00:00:00+00:00",
                    "number": "DemoX",
                    "content": {
                        "overview": " About This Course Include your long course description here.",
                        "display_name": "edX Demonstration Course",
                        "number": "DemoX"
                    },
                    "start": "1970-01-01T05:00:00+00:00",
                    "image_url": "/c4x/edX/DemoX/asset/images_course_image.jpg",
                    "org": "edX",
                    "id": "edX/DemoX/Demo_Course"
                }
            }
        ]
    };

    describe('discovery.views.CourseCard', function () {

        beforeEach(function () {
            TemplateHelpers.installTemplate('templates/discovery/course_card');
            this.view = new CourseCardView({
                model: new CourseCard(JSON_RESPONSE.results[0].data)
            });
            this.view.render();
        });

        it('renders', function () {
            var data = this.view.model.attributes;
            expect(this.view.$el).toContainHtml(data.content.display_name);
            expect(this.view.$el).toContainElement('a[href="/courses/' + data.course + '/about"]');
            expect(this.view.$el).toContainElement('img[src="' + data.image_url + '"]');
            expect(this.view.$el.find('.course-name')).toContainHtml(data.org);
            expect(this.view.$el.find('.course-name')).toContainHtml(data.content.number);
            expect(this.view.$el.find('.course-name')).toContainHtml(data.content.display_name);
            expect(this.view.$el.find('.course-date')).toContainHtml('Jan 01, 1970');
        });

    });

});
