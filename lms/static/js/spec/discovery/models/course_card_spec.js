define(['js/discovery/models/course_card'], function(CourseCard) {
    'use strict';

    describe('discovery.models.CourseCard', function () {

        beforeEach(function () {
            this.card = new CourseCard();
        });

        it('has properties', function () {
            expect(this.card.get('modes')).toBeDefined();
            expect(this.card.get('course')).toBeDefined();
            expect(this.card.get('enrollment_start')).toBeDefined();
            expect(this.card.get('number')).toBeDefined();
            expect(this.card.get('content')).toEqual({
                display_name: '',
                number: '',
                overview: ''
            });
            expect(this.card.get('start')).toBeDefined();
            expect(this.card.get('image_url')).toBeDefined();
            expect(this.card.get('org')).toBeDefined();
            expect(this.card.get('id')).toBeDefined();
        });

    });

});
