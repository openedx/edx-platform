describe "CMS.Models.Course", ->
    describe "basic", ->
        beforeEach ->
            @model = new CMS.Models.Course({
                name: "Greek Hero"
            })

        it "should take a name argument", ->
            expect(@model.get("name")).toEqual("Greek Hero")
