define ["jquery", "jasmine", "js/spec_helpers/create_sinon", "squire"],
($, jasmine, create_sinon, Squire) ->

    feedbackTpl = readFixtures('system-feedback.underscore')
    assetLibraryTpl = readFixtures('asset-library.underscore')
    assetTpl = readFixtures('asset.underscore')
    pagingHeaderTpl = readFixtures('paging-header.underscore')
    pagingFooterTpl = readFixtures('paging-footer.underscore')

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
                    @collection.url = "assets-url"
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
                expect(@model.get("locked")).toBeFalsy()
                # return an error response
                requests[0].respond(404)
                # Don't call hide because that closes the notification showing the server error.
                expect(@savingSpies.hide).not.toHaveBeenCalled()
                expect(@model.get("locked")).toBeFalsy()

    describe "Assets view", ->
        beforeEach ->
            setFixtures($("<script>", {id: "asset-library-tpl", type: "text/template"}).text(assetLibraryTpl))
            appendSetFixtures($("<script>", {id: "asset-tpl", type: "text/template"}).text(assetTpl))
            appendSetFixtures($("<script>", {id: "paging-header-tpl", type: "text/template"}).text(pagingHeaderTpl))
            appendSetFixtures($("<script>", {id: "paging-footer-tpl", type: "text/template"}).text(pagingFooterTpl))
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

            @mockAsset1 = {
                display_name: "test asset 1"
                url: 'actual_asset_url_1'
                portable_url: 'portable_url_1'
                date_added: 'date_1'
                thumbnail: null
                id: 'id_1'
            }
            @mockAsset2 = {
                display_name: "test asset 2"
                url: 'actual_asset_url_2'
                portable_url: 'portable_url_2'
                date_added: 'date_2'
                thumbnail: null
                id: 'id_2'
            }
            @mockAssetsResponse = {
                assets: [ @mockAsset1, @mockAsset2 ],
                start: 0,
                end: 1,
                page: 0,
                pageSize: 5,
                totalCount: 2
            }

            runs =>
                @injector.require ["js/models/asset", "js/collections/asset", "js/views/assets"],
                (AssetModel, AssetCollection, AssetsView) =>
                    @AssetModel = AssetModel
                    @collection = new AssetCollection();
                    @collection.url = "assets-url"
                    @view = new AssetsView
                        collection: @collection
                        el: $('#asset_table_body')
                    @view.render()

            waitsFor (=> @view), "AssetsView was not created", 1000

            $.ajax()

        afterEach ->
            delete window.analytics
            delete window.course_location_analytics

            @injector.clean()
            @injector.remove()

        addMockAsset = (requests) ->
            model = new @AssetModel
                display_name: "new asset"
                url: 'new_actual_asset_url'
                portable_url: 'portable_url'
                date_added: 'date'
                thumbnail: null
                id: 'idx'
            @view.addAsset(model)
            create_sinon.respondWithJson(requests,
                {
                    assets: [
                        @mockAsset1, @mockAsset2,
                        {
                            display_name: "new asset"
                            url: 'new_actual_asset_url'
                            portable_url: 'portable_url'
                            date_added: 'date'
                            thumbnail: null
                            id: 'idx'
                        }
                    ],
                    start: 0,
                    end: 2,
                    page: 0,
                    pageSize: 5,
                    totalCount: 3
                })


        describe "Basic", ->
            # Separate setup method to work-around mis-parenting of beforeEach methods
            setup = ->
                requests = create_sinon.requests(this)
                @view.setPage(0)
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                return requests

            $.fn.fileupload = ->
                return ''

            clickEvent = (html_selector) ->
                $(html_selector).click()

            it "should show upload modal on clicking upload asset button", ->
                spyOn(@view, "showUploadModal")
                setup.call(this)
                expect(@view.showUploadModal).not.toHaveBeenCalled()
                @view.showUploadModal(clickEvent(".upload-button"))
                expect(@view.showUploadModal).toHaveBeenCalled()

            it "should show file selection menu on choose file button", ->
                spyOn(@view, "showFileSelectionMenu")
                setup.call(this)
                expect(@view.showFileSelectionMenu).not.toHaveBeenCalled()
                @view.showFileSelectionMenu(clickEvent(".choose-file-button"))
                expect(@view.showFileSelectionMenu).toHaveBeenCalled()

            it "should hide upload modal on clicking close button", ->
                spyOn(@view, "hideModal")
                setup.call(this)
                expect(@view.hideModal).not.toHaveBeenCalled()
                @view.hideModal(clickEvent(".close-button"))
                expect(@view.hideModal).toHaveBeenCalled()

            it "should show a status indicator while loading", ->
                appendSetFixtures('<div class="ui-loading"/>')
                expect($('.ui-loading').is(':visible')).toBe(true)
                setup.call(this)
                expect($('.ui-loading').is(':visible')).toBe(false)

            it "should hide the status indicator if an error occurs while loading", ->
                requests = create_sinon.requests(this)
                appendSetFixtures('<div class="ui-loading"/>')
                expect($('.ui-loading').is(':visible')).toBe(true)
                @view.setPage(0)
                create_sinon.respondWithError(requests)
                expect($('.ui-loading').is(':visible')).toBe(false)

            it "should render both assets", ->
                requests = setup.call(this)
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).toContainText("test asset 2")

            it "should remove the deleted asset from the view", ->
                requests = setup.call(this)
                # Delete the 2nd asset with success from server.
                @view.$(".remove-asset-button")[1].click()
                @promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(@promptSpies)
                req.respond(200) for req in requests
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).not.toContainText("test asset 2")

            it "does not remove asset if deletion failed", ->
                requests = setup.call(this)
                # Delete the 2nd asset, but mimic a failure from the server.
                @view.$(".remove-asset-button")[1].click()
                @promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(@promptSpies)
                req.respond(404) for req in requests
                expect(@view.$el).toContainText("test asset 1")
                expect(@view.$el).toContainText("test asset 2")

            it "adds an asset if asset does not already exist", ->
                requests = setup.call(this)
                addMockAsset.call(this, requests)
                expect(@view.$el).toContainText("new asset")
                expect(@collection.models.length).toBe(3)

            it "does not add an asset if asset already exists", ->
                setup.call(this)
                spyOn(@collection, "add").andCallThrough()
                model = @collection.models[1]
                @view.addAsset(model)
                expect(@collection.add).not.toHaveBeenCalled()

        describe "Sorting", ->
            # Separate setup method to work-around mis-parenting of beforeEach methods
            setup = ->
                requests = create_sinon.requests(this)
                @view.setPage(0)
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                return requests

            it "should have the correct default sort order", ->
                requests = setup.call(this)
                expect(@view.sortDisplayName()).toBe("Date Added")
                expect(@view.collection.sortDirection).toBe("desc")

            it "should toggle the sort order when clicking on the currently sorted column", ->
                requests = setup.call(this)
                expect(@view.sortDisplayName()).toBe("Date Added")
                expect(@view.collection.sortDirection).toBe("desc")
                @view.$("#js-asset-date-col").click()
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                expect(@view.sortDisplayName()).toBe("Date Added")
                expect(@view.collection.sortDirection).toBe("asc")
                @view.$("#js-asset-date-col").click()
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                expect(@view.sortDisplayName()).toBe("Date Added")
                expect(@view.collection.sortDirection).toBe("desc")

            it "should switch the sort order when clicking on a different column", ->
                requests = setup.call(this)
                @view.$("#js-asset-name-col").click()
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                expect(@view.sortDisplayName()).toBe("Name")
                expect(@view.collection.sortDirection).toBe("asc")
                @view.$("#js-asset-name-col").click()
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                expect(@view.sortDisplayName()).toBe("Name")
                expect(@view.collection.sortDirection).toBe("desc")

            it "should switch sort to most recent date added when a new asset is added", ->
                requests = setup.call(this)
                @view.$("#js-asset-name-col").click()
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                addMockAsset.call(this, requests)
                create_sinon.respondWithJson(requests, @mockAssetsResponse)
                expect(@view.sortDisplayName()).toBe("Date Added")
                expect(@view.collection.sortDirection).toBe("desc")
