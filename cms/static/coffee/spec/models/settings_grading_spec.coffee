define ["underscore", "js/models/settings/course_grading_policy"], (_, CourseGradingPolicy) ->
    describe "CourseGradingPolicy", ->
        beforeEach ->
            @model = new CourseGradingPolicy()

        describe "parse", ->
            it "sets a null grace period to 00:00", ->
                attrs = @model.parse(grace_period: null)
                expect(attrs.grace_period).toEqual(
                    hours: 0,
                    minutes: 0
                )

        describe "parseGracePeriod", ->
            it "parses a time in HH:MM format", ->
                time = @model.parseGracePeriod("07:19")
                expect(time).toEqual(
                    hours: 7,
                    minutes: 19
                )

            it "returns null on an incorrectly formatted string", ->
                expect(@model.parseGracePeriod("asdf")).toBe(null)
                expect(@model.parseGracePeriod("7:19")).toBe(null)
                expect(@model.parseGracePeriod("1000:00")).toBe(null)

        describe "validate", ->
            it "enforces that the passing grade is <= the minimum grade to receive credit if credit is enabled", ->
                @model.set({minimum_grade_credit: 0.8, grace_period: '01:00', is_credit_course: true})
                @model.set('grade_cutoffs', [0.9], validate: true)
                expect(_.keys(@model.validationError)).toContain('minimum_grade_credit')

            it "does not enforce the passing grade limit in non-credit courses", ->
                @model.set({minimum_grade_credit: 0.8, grace_period: '01:00', is_credit_course: false})
                @model.set({grade_cutoffs: [0.9]}, validate: true)
                expect(@model.validationError).toBe(null)
