/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
define(["js/models/course"], Course =>
    describe("Course", () =>
        describe("basic", function() {
            beforeEach(function() {
                return this.model = new Course({
                name: "Greek Hero"
                });
            });

            return it("should take a name argument", function() {
                return expect(this.model.get("name")).toEqual("Greek Hero");
            });
        })
    )
);
