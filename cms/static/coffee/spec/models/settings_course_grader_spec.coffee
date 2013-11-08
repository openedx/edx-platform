define ["js/models/settings/course_grader"], (CourseGrader) ->
    describe "CourseGraderModel", ->
        describe "parseWeight", ->
            it "converts a float to an integer", ->
                model = new CourseGrader({weight: 7.0001, min_count: 3.67, drop_count: 1.88}, {parse:true})
                expect(model.get('weight')).toBe(7)
                expect(model.get('min_count')).toBe(3)
                expect(model.get('drop_count')).toBe(1)

            it "converts a string to an integer", ->
                model = new CourseGrader({weight: '7.0001', min_count: '3.67', drop_count: '1.88'}, {parse:true})
                expect(model.get('weight')).toBe(7)
                expect(model.get('min_count')).toBe(3)
                expect(model.get('drop_count')).toBe(1)

            it "does a no-op for integers", ->
                model = new CourseGrader({weight: 7, min_count: 3, drop_count: 1}, {parse:true})
                expect(model.get('weight')).toBe(7)
                expect(model.get('min_count')).toBe(3)
                expect(model.get('drop_count')).toBe(1)
