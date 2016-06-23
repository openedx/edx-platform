
define ["backbone", "js/models/textbook", "js/collections/textbook", "js/models/chapter", "js/collections/chapter", "js/main"],
(Backbone, Textbook, TextbookSet, Chapter, ChapterSet, main) ->

    describe "Textbook model", ->
        beforeEach ->
            main()
            @model = new Textbook()
            CMS.URL.TEXTBOOKS = "/textbooks"

        afterEach ->
            delete CMS.URL.TEXTBOOKS

        describe "Basic", ->
            it "should have an empty name by default", ->
                expect(@model.get("name")).toEqual("")

            it "should not show chapters by default", ->
                expect(@model.get("showChapters")).toBeFalsy()

            it "should have a ChapterSet with one chapter by default", ->
                chapters = @model.get("chapters")
                expect(chapters).toBeInstanceOf(ChapterSet)
                expect(chapters.length).toEqual(1)
                expect(chapters.at(0).isEmpty()).toBeTruthy()

            it "should be empty by default", ->
                expect(@model.isEmpty()).toBeTruthy()

            it "should have a URL root", ->
                urlRoot = _.result(@model, 'urlRoot')
                expect(urlRoot).toBeTruthy()

            it "should be able to reset itself", ->
                @model.set("name", "foobar")
                @model.reset()
                expect(@model.get("name")).toEqual("")

            it "should not be dirty by default", ->
                expect(@model.isDirty()).toBeFalsy()

            it "should be dirty after it's been changed", ->
                @model.set("name", "foobar")
                expect(@model.isDirty()).toBeTruthy()

            it "should not be dirty after calling setOriginalAttributes", ->
                @model.set("name", "foobar")
                @model.setOriginalAttributes()
                expect(@model.isDirty()).toBeFalsy()

        describe "Input/Output", ->
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
                    "editing": false,
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

                model = new Textbook(serverModelSpec, {parse: true})
                expect(deepAttributes(model)).toEqual(clientModelSpec)
                expect(model.toJSON()).toEqual(serverModelSpec)

        describe "Validation", ->
            it "requires a name", ->
                model = new Textbook({name: ""})
                expect(model.isValid()).toBeFalsy()

            it "requires at least one chapter", ->
                model = new Textbook({name: "foo"})
                model.get("chapters").reset()
                expect(model.isValid()).toBeFalsy()

            it "requires a valid chapter", ->
                chapter = new Chapter()
                chapter.isValid = -> false
                model = new Textbook({name: "foo"})
                model.get("chapters").reset([chapter])
                expect(model.isValid()).toBeFalsy()

            it "requires all chapters to be valid", ->
                chapter1 = new Chapter()
                chapter1.isValid = -> true
                chapter2 = new Chapter()
                chapter2.isValid = -> false
                model = new Textbook({name: "foo"})
                model.get("chapters").reset([chapter1, chapter2])
                expect(model.isValid()).toBeFalsy()

            it "can pass validation", ->
                chapter = new Chapter()
                chapter.isValid = -> true
                model = new Textbook({name: "foo"})
                model.get("chapters").reset([chapter])
                expect(model.isValid()).toBeTruthy()


    describe "Textbook collection", ->
        beforeEach ->
            CMS.URL.TEXTBOOKS = "/textbooks"
            @collection = new TextbookSet()

        afterEach ->
            delete CMS.URL.TEXTBOOKS

        it "should have a url set", ->
            url = _.result(@collection, 'url')
            expect(url).toEqual("/textbooks")


    describe "Chapter model", ->
        beforeEach ->
            @model = new Chapter()

        describe "Basic", ->
            it "should have a name by default", ->
                expect(@model.get("name")).toEqual("")

            it "should have an asset_path by default", ->
                expect(@model.get("asset_path")).toEqual("")

            it "should have an order by default", ->
                expect(@model.get("order")).toEqual(1)

            it "should be empty by default", ->
                expect(@model.isEmpty()).toBeTruthy()

        describe "Validation", ->
            it "requires a name", ->
                model = new Chapter({name: "", asset_path: "a.pdf"})
                expect(model.isValid()).toBeFalsy()

            it "requires an asset_path", ->
                model = new Chapter({name: "a", asset_path: ""})
                expect(model.isValid()).toBeFalsy()

            it "can pass validation", ->
                model = new Chapter({name: "a", asset_path: "a.pdf"})
                expect(model.isValid()).toBeTruthy()


    describe "Chapter collection", ->
        beforeEach ->
            @collection = new ChapterSet()

        it "is empty by default", ->
            expect(@collection.isEmpty()).toBeTruthy()

        it "is empty if all chapters are empty", ->
            @collection.add([{}, {}, {}])
            expect(@collection.isEmpty()).toBeTruthy()

        it "is not empty if a chapter is not empty", ->
            @collection.add([{}, {name: "full"}, {}])
            expect(@collection.isEmpty()).toBeFalsy()

        it "should have a nextOrder function", ->
            expect(@collection.nextOrder()).toEqual(1)
            @collection.add([{}])
            expect(@collection.nextOrder()).toEqual(2)
            @collection.add([{}])
            expect(@collection.nextOrder()).toEqual(3)
            # verify that it doesn't just return an incrementing value each time
            expect(@collection.nextOrder()).toEqual(3)
            # try going back one
            @collection.remove(@collection.last())
            expect(@collection.nextOrder()).toEqual(2)
