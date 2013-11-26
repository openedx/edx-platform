define ["js/models/course"], (Course) ->
    describe "Course", ->
        describe "basic", ->
            beforeEach ->
                @model = new Course({
                name: "Greek Hero"
                })

            it "should take a name argument", ->
                expect(@model.get("name")).toEqual("Greek Hero")
