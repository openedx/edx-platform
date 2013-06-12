describe "CMS.Models.Textbook", ->
    beforeEach ->
        @model = new CMS.Models.Textbook()

    it "should have an empty name by default", ->
        expect(@model.get("name")).toEqual("")

    it "should not show chapters by default", ->
        expect(@model.get("showChapters")).toBeFalsy()

    it "should have a ChapterSet with one chapter by default", ->
        expect(@model.get("chapters").length).toEqual(1)
