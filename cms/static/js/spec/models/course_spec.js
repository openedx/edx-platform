define(["js/models/course"], Course =>
    describe("Course", () =>
        describe("basic", function() {
            beforeEach(function() {
                this.model = new Course({
                name: "Greek Hero"
                });
            });

            it("should take a name argument", function() {
                expect(this.model.get("name")).toEqual("Greek Hero");
            });
        })
    )
);
