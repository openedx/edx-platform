beforeEach ->
    @addMatchers
        toBeInstanceOf: (expected) ->
            return @actual instanceof expected


describe "CMS.Models.Textbook", ->
    beforeEach ->
        @model = new CMS.Models.Textbook()

    it "should have an empty name by default", ->
        expect(@model.get("name")).toEqual("")

    it "should not show chapters by default", ->
        expect(@model.get("showChapters")).toBeFalsy()

    it "should have a ChapterSet with one chapter by default", ->
        chapters = @model.get("chapters")
        expect(chapters).toBeInstanceOf(CMS.Collections.ChapterSet)
        expect(chapters.length).toEqual(1)

    it "should be empty by default", ->
        expect(@model.isEmpty()).toBeTruthy()


describe "CMS.Models.Textbook input/output", ->
    # replace with Backbone.Assocations.deepAttributes when
    # https://github.com/dhruvaray/backbone-associations/pull/43 is merged
    deepAttributes = (obj) ->
        if obj instanceof Backbone.Model
            deepAttributes(obj.attributes)
        else if obj instanceof Backbone.Collection
            obj.map(deepAttributes);
        else if _.isArray(obj)
            _.map(obj, deepAttributes);
        else if _.isObject(obj)
            attributes = {};
            for own prop, val of obj
                attributes[prop] = deepAttributes(val)
            attributes
        else
            obj

    it "should match server model to client model", ->
        serverModelSpec = {
            "tab_title": "My Textbook",
            "chapters": [
                {"title": "Chapter 1", "url": "/ch1.pdf"},
                {"title": "Chapter 2", "url": "/ch2.pdf"},
            ]
        }
        clientModelSpec = {
            "name": "My Textbook",
            "showChapters": false,
            "chapters": [{
                    "name": "Chapter 1",
                    "asset_path": "/ch1.pdf",
                    "order": 1
                }, {
                    "name": "Chapter 2",
                    "asset_path": "/ch2.pdf",
                    "order": 2
                }
            ]
        }

        model = new CMS.Models.Textbook(serverModelSpec, {parse: true})
        expect(deepAttributes(model)).toEqual(clientModelSpec)
        expect(model.toJSON()).toEqual(serverModelSpec)
