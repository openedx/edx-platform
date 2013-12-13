define ["jasmine", "js/spec/create_sinon", "squire"],
(jasmine, create_sinon, Squire) ->

    feedbackTpl = readFixtures('system-feedback.underscore')
    assetTpl = readFixtures('asset.underscore')

    describe "Asset view", ->
        beforeEach ->
            setFixtures($("<script>", {id: "asset-tpl", type: "text/template"}).text(assetTpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            appendSetFixtures(sandbox({id: "page-prompt"}))

            @promptSpies = jasmine.createSpyObj('Prompt.Warning', ["constructor", "show", "hide"])
            @promptSpies.constructor.andReturn(@promptSpies)
            @promptSpies.show.andReturn(@promptSpies)

            @confirmationSpies = jasmine.createSpyObj('Notification.Confirmation', ["constructor", "show"])
            @confirmationSpies.constructor.andReturn(@confirmationSpies)
            @confirmationSpies.show.andReturn(@confirmationSpies)

            @savingSpies = jasmine.createSpyObj('Notification.Mini', ["constructor", "show", "hide"])
            @savingSpies.constructor.andReturn(@savingSpies)
            @savingSpies.show.andReturn(@savingSpies)

            @injector = new Squire()
            @injector.mock("js/views/feedback_prompt", {
                "Warning": @promptSpies.constructor
            })
            @injector.mock("js/views/feedback_notification", {
                "Confirmation": @confirmationSpies.constructor,
                "Mini": @savingSpies.constructor
            })
            runs =>
                @injector.require ["js/models/asset", "js/collections/asset", "js/views/asset"],
                (AssetModel, AssetCollection, AssetView) =>
                    @model = new AssetModel
                        display_name: "test asset"
                        url: 'actual_asset_url'
                        portable_url: 'portable_url'
                        date_added: 'date'
                        thumbnail: null
                        id: 'id'
                    spyOn(@model, "destroy").andCallThrough()
                    spyOn(@model, "save").andCallThrough()

                    @collection = new AssetCollection([@model])
                    @collection.url = "update-asset-url"
                    @view = new AssetView({model: @model})

            waitsFor (=> @view), "AssetView was not created", 1000

        afterEach ->
            @injector.clean()
            @injector.remove()

        describe "Basic", ->
            it "should render properly", ->
                @view.render()
                expect(@view.$el).toContainText("test asset")

            it "should pop a delete confirmation when the delete button is clicked", ->
                @view.render().$(".remove-asset-button").click()
                expect(@promptSpies.constructor).toHaveBeenCalled()
                ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
                expect(ctorOptions.title).toMatch('Delete File Confirmation')
                # hasn't actually been removed
                expect(@model.destroy).not.toHaveBeenCalled()
                expect(@collection).toContain(@model)

        describe "AJAX", ->
            it "should destroy itself on confirmation", ->
                requests = create_sinon["requests"](this)

                @view.render().$(".remove-asset-button").click()
                ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
                # run the primary function to indicate confirmation
                ctorOptions.actions.primary.click(@promptSpies)
                # AJAX request has been sent, but not yet returned
                expect(@model.destroy).toHaveBeenCalled()
                expect(requests.length).toEqual(1)
                expect(@confirmationSpies.constructor).not.toHaveBeenCalled()
                expect(@collection.contains(@model)).toBeTruthy()
                # return a success response
                requests[0].respond(200)
                expect(@confirmationSpies.constructor).toHaveBeenCalled()
                expect(@confirmationSpies.show).toHaveBeenCalled()
                savingOptions = @confirmationSpies.constructor.mostRecentCall.args[0]
                expect(savingOptions.title).toMatch("Your file has been deleted.")
                expect(@collection.contains(@model)).toBeFalsy()

            it "should not destroy itself if server errors", ->
                requests = create_sinon["requests"](this)

                @view.render().$(".remove-asset-button").click()
                ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
                # run the primary function to indicate confirmation
                ctorOptions.actions.primary.click(@promptSpies)
                # AJAX request has been sent, but not yet returned
                expect(@model.destroy).toHaveBeenCalled()
                # return an error response
                requests[0].respond(404)
                expect(@confirmationSpies.constructor).not.toHaveBeenCalled()
                expect(@collection.contains(@model)).toBeTruthy()

            it "should lock the asset on confirmation", ->
                requests = create_sinon["requests"](this)

                @view.render().$(".lock-checkbox").click()
                # AJAX request has been sent, but not yet returned
                expect(@model.save).toHaveBeenCalled()
                expect(requests.length).toEqual(1)
                expect(@savingSpies.constructor).toHaveBeenCalled()
                expect(@savingSpies.show).toHaveBeenCalled()
                savingOptions = @savingSpies.constructor.mostRecentCall.args[0]
                expect(savingOptions.title).toMatch("Saving...")
                expect(@model.get("locked")).toBeFalsy()
                # return a success response
                requests[0].respond(200)
                expect(@savingSpies.hide).toHaveBeenCalled()
                expect(@model.get("locked")).toBeTruthy()

            it "should not lock the asset if server errors", ->
                requests = create_sinon["requests"](this)

                @view.render().$(".lock-checkbox").click()
                # return an error response
                requests[0].respond(404)
                # Don't call hide because that closes the notification showing the server error.
                expect(@savingSpies.hide).not.toHaveBeenCalled()
                expect(@model.get("locked")).toBeFalsy()

    describe "Assets view", ->
        beforeEach ->
            setFixtures($("<script>", {id: "asset-tpl", type: "text/template"}).text(assetTpl))
            window.analytics = jasmine.createSpyObj('analytics', ['track'])
            window.course_location_analytics = jasmine.createSpy()
            appendSetFixtures(sandbox({id: "asset_table_body"}))

            @promptSpies = jasmine.createSpyObj('Prompt.Warning', ["constructor", "show", "hide"])
            @promptSpies.constructor.andReturn(@promptSpies)
            @promptSpies.show.andReturn(@promptSpies)

            @injector = new Squire()
            @injector.mock("js/views/feedback_prompt", {
                "Warning": @promptSpies.constructor
            })

            runs =>
                @injector.require ["js/models/asset", "js/collections/asset", "js/views/assets"],
                (AssetModel, AssetCollection, AssetsView) =>
                    @AssetModel = AssetModel
                    @collection = new AssetCollection [
                            display_name: "test asset 1"
                            url: 'actual_asset_url_1'
                            portable_url: 'portable_url_1'
                            date_added: 'date_1'
                            thumbnail: null
                            id: 'id_1'
                        ,
                            display_name: "test asset 2"
                            url: 'actual_asset_url_2'
                            portable_url: 'portable_url_2'
                            date_added: 'date_2'
                            thumbnail: null
                            id: 'id_2'
                        ]
                    @collection.url = "update-asset-url"
                    @view = new AssetsView
                        collection: @collection
                        el: $('#asset_table_body')

            waitsFor (=> @view), "AssetView was not created", 1000

            $.ajax()

        afterEach ->
            delete window.analytics
            delete window.course_location_analytics

            @injector.clean()
            @injector.remove()

        describe "Basic", ->
            it "should render both assets", ->
                @view.render()
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).toContainText("test asset 2")

            it "should remove the deleted asset from the view", ->
                requests = create_sinon["requests"](this)

                # Delete the 2nd asset with success from server.
                @view.render().$(".remove-asset-button")[1].click()
                @promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(@promptSpies)
                req.respond(200) for req in requests
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).not.toContainText("test asset 2")

            it "does not remove asset if deletion failed", ->
                requests = create_sinon["requests"](this)

                # Delete the 2nd asset, but mimic a failure from the server.
                @view.render().$(".remove-asset-button")[1].click()
                @promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(@promptSpies)
                req.respond(404) for req in requests
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).toContainText("test asset 2")

            it "adds an asset if asset does not already exist", ->
                @view.render()
                model = new @AssetModel
                    display_name: "new asset"
                    url: 'new_actual_asset_url'
                    portable_url: 'portable_url'
                    date_added: 'date'
                    thumbnail: null
                    id: 'idx'
                @view.addAsset(model)
                expect(@view.$el).toContainText("new asset")
                expect(@collection.models.indexOf(model)).toBe(0)
                expect(@collection.models.length).toBe(3)

            it "does not add an asset if asset already exists", ->
                @view.render()
                spyOn(@collection, "add").andCallThrough()
                model = @collection.models[1]
                @view.addAsset(model)
                expect(@collection.add).not.toHaveBeenCalled()
