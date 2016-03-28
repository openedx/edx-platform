define([
    'js/models/settings/course_grader', 'js/collections/course_grader'
], function (CourseGrader, CourseGraderCollection) {
    'use strict';
    describe('CourseGraderModel', function() {
        it('converts a float to an integer', function() {
            var model = new CourseGrader({
                weight: 7.0001, passing_grade: 10.0001, min_count: 3.67, drop_count: 1.88
            }, {parse:true});
            expect(model.get('weight')).toBe(7);
            expect(model.get('passing_grade')).toBe(10);
            expect(model.get('min_count')).toBe(4);
            expect(model.get('drop_count')).toBe(2);
        });

        it('converts float value of weight to an integer with rounding', function() {
            var model = new CourseGrader({weight:  28.999999999999996}, {parse:true});
            expect(model.get('weight')).toBe(29);
        });

        it('converts float value of passing_grade to an integer with rounding', function() {
            var model = new CourseGrader({passing_grade:  28.999999999999996}, {parse:true});
            expect(model.get('passing_grade')).toBe(29);
        });

        it('converts a string to an integer', function() {
            var model = new CourseGrader({
                weight: '7.0001', passing_grade: '10.0001', min_count: '3.67', drop_count: '1.88'
            }, {parse:true});
            expect(model.get('weight')).toBe(7);
            expect(model.get('passing_grade')).toBe(10);
            expect(model.get('min_count')).toBe(4);
            expect(model.get('drop_count')).toBe(2);
        });

        it('does a no-op for integers', function() {
            var model = new CourseGrader({
                weight: 7, passing_grade: 10, min_count: 3, drop_count: 1
            }, {parse:true});
            expect(model.get('weight')).toBe(7);
            expect(model.get('passing_grade')).toBe(10);
            expect(model.get('min_count')).toBe(3);
            expect(model.get('drop_count')).toBe(1);
        });

        describe('validation', function () {
            it('gives an error if type is an empty string', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({type: ''}, {validate:true});
                expect(errors.type).toBe('The assignment type must have a name.');
            });

            it('gives an error if another type with the same name already exists', function() {
                var collection = new CourseGraderCollection([{}, {type: 'abc'}], {parse: true}),
                    model = collection.at(0), errors;
                errors = model.validate({type: 'abc'}, {validate:true});
                expect(errors.type).toBe('There\'s already another assignment type with this name.');
            });

            it('gives an error if weight is less than 0 or higher than 100', function() {
                var model = new CourseGrader(), errors;
                // don't allow negative integers
                errors = model.validate({weight: -12}, {validate:true});
                expect(errors.weight).toBe('Please enter an integer between 0 and 100.');
                // don't allow value greater then 100
                errors = model.validate({weight: 101}, {validate:true});
                expect(errors.weight).toBe('Please enter an integer between 0 and 100.');
            });

            it('gives an error if weight is not a number', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({weight: 'abc'}, {validate:true});
                expect(errors.weight).toBe('Please enter an integer between 0 and 100.');
            });

            it('gives an error if weight is string with only spaces', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({weight: ' '}, {validate:true});
                expect(errors.weight).toBe('Please enter an integer between 0 and 100.');
            });

            it('gives an error if weight is float number', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({weight: '10.5'}, {validate:true});
                expect(errors.weight).toBe('Please enter an integer between 0 and 100.');
            });

            it('gives an error if passing_grade is less than 1 or higher than 100', function() {
                var model = new CourseGrader(), errors;
                // don't allow negative integers
                errors = model.validate({passing_grade: -12}, {validate:true});
                expect(errors.passing_grade).toBe('Please enter an integer between 1 and 100.');
                // don't allow value more then 100
                errors = model.validate({passing_grade: 101}, {validate:true});
                expect(errors.passing_grade).toBe('Please enter an integer between 1 and 100.');
            });

            it('gives an error if passing_grade is not a number', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({passing_grade: 'abc'}, {validate:true});
                expect(errors.passing_grade).toBe('Please enter an integer between 1 and 100.');
            });

            it('gives an error if passing_grade is empty or string with only spaces', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({passing_grade: ''}, {validate:true});
                expect(errors.passing_grade).toBe('Please enter an integer between 1 and 100.');
                errors = model.validate({passing_grade: '  '}, {validate:true});
                expect(errors.passing_grade).toBe('Please enter an integer between 1 and 100.');
            });

            it('gives an error if min_count is less than 1 or drop_count is NaN', function() {
                var model = new CourseGrader(), errors;
                errors = model.validate({min_count: 0, drop_count: ''}, {validate:true});
                expect(errors.min_count).toBe('Please enter an integer greater than 0.');
                expect(errors.drop_count).toBe('Please enter non-negative integer.');
                // don't allow negative integers
                errors = model.validate({min_count: -12, drop_count: -1}, {validate:true});
                expect(errors.min_count).toBe('Please enter an integer greater than 0.');
                expect(errors.drop_count).toBe('Please enter non-negative integer.');
                // don't allow floats
                errors = model.validate({min_count: 12.2, drop_count: 1.5}, {validate:true});
                expect(errors.min_count).toBe('Please enter an integer greater than 0.');
                expect(errors.drop_count).toBe('Please enter non-negative integer.');
            });
        });
    });
});
