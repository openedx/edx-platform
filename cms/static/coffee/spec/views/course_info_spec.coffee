define ["js/views/course_info_handout", "js/views/course_info_update", "js/models/module_info", "js/collections/course_update", "sinon"],
(CourseInfoHandoutsView, CourseInfoUpdateView, ModuleInfo, CourseUpdateCollection, sinon) ->

    courseInfoPage = """
                     <div class="course-info-wrapper">
                     <div class="main-column window">
                     <article class="course-updates" id="course-update-view">
                     <ol class="update-list" id="course-update-list"></ol>
                     </article>
                     </div>
                     <div class="sidebar window course-handouts" id="course-handouts-view"></div>
                     </div>
                     <div class="modal-cover"></div>
                     """

    beforeEach ->
        window.analytics = jasmine.createSpyObj('analytics', ['track'])
        window.course_location_analytics = jasmine.createSpy()

    afterEach ->
        delete window.analytics
        delete window.course_location_analytics

    describe "Course Updates", ->
        courseInfoTemplate = readFixtures('course_info_update.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "course_info_update-tpl", type: "text/template"}).text(courseInfoTemplate))
            appendSetFixtures courseInfoPage

            courseUpdatesXhr = sinon.useFakeXMLHttpRequest()
            @courseUpdatesRequests = requests = []
            courseUpdatesXhr.onCreate = (xhr) -> requests.push(xhr)
            @xhrRestore = courseUpdatesXhr.restore

            @collection = new CourseUpdateCollection()
            @collection.url = 'course_info_update/'
            @courseInfoEdit = new CourseInfoUpdateView({
                el: $('.course-updates'),
                collection: @collection,
                base_asset_url : 'base-asset-url/'
            })

            @courseInfoEdit.render()

            @event = {
                preventDefault : () -> 'no op'
            }

            @createNewUpdate = (text) ->
                # Edit button is not in the template under test (it is in parent HTML).
                # Therefore call onNew directly.
                @courseInfoEdit.onNew(@event)
                spyOn(@courseInfoEdit.$codeMirror, 'getValue').andReturn(text)
                @courseInfoEdit.$el.find('.save-button').click()

            @cancelNewCourseInfo = (useCancelButton) ->
                @courseInfoEdit.onNew(@event)
                spyOn(@courseInfoEdit.$modalCover, 'hide').andCallThrough()

                spyOn(@courseInfoEdit.$codeMirror, 'getValue').andReturn('unsaved changes')
                model = @collection.at(0)
                spyOn(model, "save").andCallThrough()

                cancelEditingUpdate(@courseInfoEdit, @courseInfoEdit.$modalCover, useCancelButton)

                expect(@courseInfoEdit.$modalCover.hide).toHaveBeenCalled()
                expect(model.save).not.toHaveBeenCalled()
                previewContents = @courseInfoEdit.$el.find('.update-contents').html()
                expect(previewContents).not.toEqual('unsaved changes')

            @cancelExistingCourseInfo = (useCancelButton) ->
                @createNewUpdate('existing update')
                @courseInfoEdit.$el.find('.edit-button').click()
                spyOn(@courseInfoEdit.$modalCover, 'hide').andCallThrough()

                spyOn(@courseInfoEdit.$codeMirror, 'getValue').andReturn('modification')
                model = @collection.at(0)
                spyOn(model, "save").andCallThrough()
                model.id = "saved_to_server"
                cancelEditingUpdate(@courseInfoEdit, @courseInfoEdit.$modalCover, useCancelButton)

                expect(@courseInfoEdit.$modalCover.hide).toHaveBeenCalled()
                expect(model.save).not.toHaveBeenCalled()
                previewContents = @courseInfoEdit.$el.find('.update-contents').html()
                expect(previewContents).toEqual('existing update')

            cancelEditingUpdate = (update, modalCover, useCancelButton) ->
                if useCancelButton
                    update.$el.find('.cancel-button').click()
                else
                    modalCover.click()

        afterEach ->
            @xhrRestore()

        it "does not rewrite links on save", ->
            # Create a new update, verifying that the model is created
            # in the collection and save is called.
            expect(@collection.isEmpty()).toBeTruthy()
            @courseInfoEdit.onNew(@event)
            expect(@collection.length).toEqual(1)
            model = @collection.at(0)
            spyOn(model, "save").andCallThrough()
            spyOn(@courseInfoEdit.$codeMirror, 'getValue').andReturn('/static/image.jpg')

            # Click the "Save button."
            @courseInfoEdit.$el.find('.save-button').click()
            expect(model.save).toHaveBeenCalled()

            # Verify content sent to server does not have rewritten links.
            contentSaved = JSON.parse(@courseUpdatesRequests[@courseUpdatesRequests.length - 1].requestBody).content
            expect(contentSaved).toEqual('/static/image.jpg')

        it "does rewrite links for preview", ->
            # Create a new update.
            @createNewUpdate('/static/image.jpg')

            # Verify the link is rewritten for preview purposes.
            previewContents = @courseInfoEdit.$el.find('.update-contents').html()
            expect(previewContents).toEqual('base-asset-url/image.jpg')

        it "shows static links in edit mode", ->
            @createNewUpdate('/static/image.jpg')

            # Click edit and verify CodeMirror contents.
            @courseInfoEdit.$el.find('.edit-button').click()
            expect(@courseInfoEdit.$codeMirror.getValue()).toEqual('/static/image.jpg')

        it "removes newly created course info on cancel", ->
            @cancelNewCourseInfo(true)

        it "removes newly created course info on click outside modal", ->
            @cancelNewCourseInfo(false)

        it "does not remove existing course info on cancel", ->
            @cancelExistingCourseInfo(true)

        it "does not remove existing course info on click outside modal", ->
            @cancelExistingCourseInfo(false)

    describe "Course Handouts", ->
        handoutsTemplate = readFixtures('course_info_handouts.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "course_info_handouts-tpl", type: "text/template"}).text(handoutsTemplate))
            appendSetFixtures courseInfoPage

            courseHandoutsXhr = sinon.useFakeXMLHttpRequest()
            @handoutsRequests = requests = []
            courseHandoutsXhr.onCreate = (xhr) -> requests.push(xhr)
            @handoutsXhrRestore = courseHandoutsXhr.restore

            @model = new ModuleInfo({
                id: 'handouts-id',
                data: '/static/fromServer.jpg'
            })

            @handoutsEdit = new CourseInfoHandoutsView({
                el: $('#course-handouts-view'),
                model: @model,
                base_asset_url: 'base-asset-url/'
            });

            @handoutsEdit.render()

        afterEach ->
            @handoutsXhrRestore()

        it "does not rewrite links on save", ->
            # Enter something in the handouts section, verifying that the model is saved
            # when "Save" is clicked.
            @handoutsEdit.$el.find('.edit-button').click()
            spyOn(@handoutsEdit.$codeMirror, 'getValue').andReturn('/static/image.jpg')
            spyOn(@model, "save").andCallThrough()
            @handoutsEdit.$el.find('.save-button').click()
            expect(@model.save).toHaveBeenCalled()

            contentSaved = JSON.parse(@handoutsRequests[@handoutsRequests.length - 1].requestBody).data
            expect(contentSaved).toEqual('/static/image.jpg')

        it "does rewrite links in initial content", ->
            expect(@handoutsEdit.$preview.html().trim()).toBe('base-asset-url/fromServer.jpg')

        it "does rewrite links after edit", ->
            # Edit handouts and save.
            @handoutsEdit.$el.find('.edit-button').click()
            spyOn(@handoutsEdit.$codeMirror, 'getValue').andReturn('/static/image.jpg')
            @handoutsEdit.$el.find('.save-button').click()

            # Verify preview text.
            expect(@handoutsEdit.$preview.html().trim()).toBe('base-asset-url/image.jpg')

        it "shows static links in edit mode", ->
            # Click edit and verify CodeMirror contents.
            @handoutsEdit.$el.find('.edit-button').click()
            expect(@handoutsEdit.$codeMirror.getValue().trim()).toEqual('/static/fromServer.jpg')

