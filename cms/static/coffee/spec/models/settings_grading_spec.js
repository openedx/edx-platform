/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
define(["underscore", "js/models/settings/course_grading_policy"], (_, CourseGradingPolicy) =>
    describe("CourseGradingPolicy", function() {
        beforeEach(function() {
            return this.model = new CourseGradingPolicy();
        });

        describe("parse", () =>
            it("sets a null grace period to 00:00", function() {
                const attrs = this.model.parse({grace_period: null});
                return expect(attrs.grace_period).toEqual({
                    hours: 0,
                    minutes: 0
                });
            })
        );

        describe("parseGracePeriod", function() {
            it("parses a time in HH:MM format", function() {
                const time = this.model.parseGracePeriod("07:19");
                return expect(time).toEqual({
                    hours: 7,
                    minutes: 19
                });
            });

            return it("returns null on an incorrectly formatted string", function() {
                expect(this.model.parseGracePeriod("asdf")).toBe(null);
                expect(this.model.parseGracePeriod("7:19")).toBe(null);
                return expect(this.model.parseGracePeriod("1000:00")).toBe(null);
            });
        });

        return describe("validate", function() {
            it("enforces that the passing grade is <= the minimum grade to receive credit if credit is enabled", function() {
                this.model.set({minimum_grade_credit: 0.8, grace_period: '01:00', is_credit_course: true});
                this.model.set('grade_cutoffs', [0.9], {validate: true});
                return expect(_.keys(this.model.validationError)).toContain('minimum_grade_credit');
            });

            return it("does not enforce the passing grade limit in non-credit courses", function() {
                this.model.set({minimum_grade_credit: 0.8, grace_period: '01:00', is_credit_course: false});
                this.model.set({grade_cutoffs: [0.9]}, {validate: true});
                return expect(this.model.validationError).toBe(null);
            });
        });
    })
);
