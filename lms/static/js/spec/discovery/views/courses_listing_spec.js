define([
    'jquery', 'backbone', 'common/js/spec_helpers/template_helpers',
    'js/discovery/models/course_card', 'js/discovery/views/courses_listing'
], function($, Backbone, TemplateHelpers, CourseCard, CoursesListing) {
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


    describe('discovery.views.CoursesListing', function () {

        beforeEach(function () {
            jasmine.clock().install();
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplate('templates/discovery/course_card');
            var collection = new Backbone.Collection(
                [JSON_RESPONSE.results[0].data],
                { model: CourseCard }
            );
            var mock = {
                collection: collection,
                latest: function () { return this.collection.last(20); }
            };
            this.view = new CoursesListing({ model: mock });
        });

        afterEach(function() {
            jasmine.clock().uninstall();
        });

        it('renders search results', function () {
            this.view.render();
            expect($('.courses-listing article').length).toEqual(1);
            expect($('.courses-listing .course-title')).toContainHtml('edX Demonstration Course');
            this.view.renderNext();
            expect($('.courses-listing article').length).toEqual(2);
        });

        it('scrolling triggers an event for next page', function () {
            this.onNext = jasmine.createSpy('onNext');
            this.view.on('next', this.onNext);
            this.view.render();
            window.scroll(0, $(document).height());
            $(window).trigger('scroll');
            jasmine.clock().tick(500);
            expect(this.onNext).toHaveBeenCalled();

            // should not be triggered again (while it is loading)
            $(window).trigger('scroll');
            jasmine.clock().tick(500);
            expect(this.onNext.calls.count()).toEqual(1);
        });

    });

});
