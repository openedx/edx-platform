define ["js/views/course_info_handout", "js/views/course_info_update", "js/models/module_info", 
        "js/collections/course_update", "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers"],
(CourseInfoHandoutsView, CourseInfoUpdateView, ModuleInfo, CourseUpdateCollection, AjaxHelpers) ->

    describe "Course Updates and Handouts", ->
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

        describe "Course Updates without Push notification", ->
            courseInfoTemplate = readFixtures('course_info_update.underscore')

            beforeEach ->
                setFixtures($("<script>", {id: "course_info_update-tpl", type: "text/template"}).text(courseInfoTemplate))
                appendSetFixtures courseInfoPage

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
                    spyOn(@courseInfoEdit.$codeMirror, 'getValue').and.returnValue(text)
                    @courseInfoEdit.$el.find('.save-button').click()

                @cancelNewCourseInfo = (useCancelButton) ->
                    @courseInfoEdit.onNew(@event)
                    spyOn(@courseInfoEdit.$modalCover, 'hide').and.callThrough()

                    spyOn(@courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes')
                    model = @collection.at(0)
                    spyOn(model, "save").and.callThrough()

                    cancelEditingUpdate(@courseInfoEdit, @courseInfoEdit.$modalCover, useCancelButton)

                    expect(@courseInfoEdit.$modalCover.hide).toHaveBeenCalled()
                    expect(model.save).not.toHaveBeenCalled()
                    previewContents = @courseInfoEdit.$el.find('.update-contents').html()
                    expect(previewContents).not.toEqual('unsaved changes')

                @doNotCloseNewCourseInfo = () ->
                    @courseInfoEdit.onNew(@event)
                    spyOn(@courseInfoEdit.$modalCover, 'hide').and.callThrough()

                    spyOn(@courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes')
                    model = @collection.at(0)
                    spyOn(model, "save").and.callThrough()

                    cancelEditingUpdate(@courseInfoEdit, @courseInfoEdit.$modalCover, false)

                    expect(model.save).not.toHaveBeenCalled()
                    expect(@courseInfoEdit.$modalCover.hide).not.toHaveBeenCalled()

                @cancelExistingCourseInfo = (useCancelButton) ->
                    @createNewUpdate('existing update')
                    @courseInfoEdit.$el.find('.edit-button').click()
                    spyOn(@courseInfoEdit.$modalCover, 'hide').and.callThrough()

                    spyOn(@courseInfoEdit.$codeMirror, 'getValue').and.returnValue('modification')
                    model = @collection.at(0)
                    spyOn(model, "save").and.callThrough()
                    model.id = "saved_to_server"
                    cancelEditingUpdate(@courseInfoEdit, @courseInfoEdit.$modalCover, useCancelButton)

                    expect(@courseInfoEdit.$modalCover.hide).toHaveBeenCalled()
                    expect(model.save).not.toHaveBeenCalled()
                    previewContents = @courseInfoEdit.$el.find('.update-contents').html()
                    expect(previewContents).toEqual('existing update')

                @testInvalidDateValue = (value) ->
                    @courseInfoEdit.onNew(@event)
                    expect(@courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(false)
                    @courseInfoEdit.$el.find('input.date').val(value).trigger("change")
                    expect(@courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(true)
                    @courseInfoEdit.$el.find('input.date').val("01/01/16").trigger("change")
                    expect(@courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(false)

                cancelEditingUpdate = (update, modalCover, useCancelButton) ->
                    if useCancelButton
                        update.$el.find('.cancel-button').click()
                    else
                        modalCover.click()

            it "does send expected data on save", ->
                requests = AjaxHelpers["requests"](this)

                # Create a new update, verifying that the model is created
                # in the collection and save is called.
                expect(@collection.isEmpty()).toBeTruthy()
                @courseInfoEdit.onNew(@event)
                expect(@collection.length).toEqual(1)
                model = @collection.at(0)
                spyOn(model, "save").and.callThrough()
                spyOn(@courseInfoEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg')

                # Click the "Save button."
                @courseInfoEdit.$el.find('.save-button').click()
                expect(model.save).toHaveBeenCalled()

                # Verify push_notification_selected is set to false.
                requestSent = JSON.parse(requests[requests.length - 1].requestBody)
                expect(requestSent.push_notification_selected).toEqual(false)

                # Verify the link is not rewritten when saved.
                expect(requestSent.content).toEqual('/static/image.jpg')

                # Verify that analytics are sent
                expect(window.analytics.track).toHaveBeenCalled()

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

            it "do not close new course info on click outside modal", ->
                @doNotCloseNewCourseInfo()

            it "does not remove existing course info on cancel", ->
                @cancelExistingCourseInfo(true)

            it "does not remove existing course info on click outside modal", ->
                @cancelExistingCourseInfo(false)

            it "does not allow updates to be saved with an invalid date", ->
                @testInvalidDateValue("Marchtober 40, 2048")

            it "does not allow updates to be saved with a blank date", ->
                @testInvalidDateValue("")


        describe "Course Updates WITH Push notification", ->
            courseInfoTemplate = readFixtures('course_info_update.underscore')

            beforeEach ->
                setFixtures($("<script>", {id: "course_info_update-tpl", type: "text/template"}).text(courseInfoTemplate))
                appendSetFixtures courseInfoPage
                @collection = new CourseUpdateCollection()
                @collection.url = 'course_info_update/'
                @courseInfoEdit = new CourseInfoUpdateView({
                    el: $('.course-updates'),
                    collection: @collection,
                    base_asset_url : 'base-asset-url/',
                    push_notification_enabled : true
                })
                @courseInfoEdit.render()
                @event = {preventDefault : () -> 'no op'}
                @courseInfoEdit.onNew(@event)

            it "shows push notification checkbox as selected by default", ->
                expect(@courseInfoEdit.$el.find('.toggle-checkbox')).toBeChecked()

            it "sends correct default value for push_notification_selected", ->
                requests = AjaxHelpers.requests(this);
                @courseInfoEdit.$el.find('.save-button').click()
                requestSent = JSON.parse(requests[requests.length - 1].requestBody)
                expect(requestSent.push_notification_selected).toEqual(true)

		# Check that analytics send push_notification info
                analytics_payload = window.analytics.track.calls.first().args[1]
                expect(analytics_payload).toEqual(jasmine.objectContaining({'push_notification_selected': true}))

            it "sends correct value for push_notification_selected when it is unselected", ->
                requests = AjaxHelpers.requests(this);
                # unselect push notification
                @courseInfoEdit.$el.find('.toggle-checkbox').attr('checked', false);
                @courseInfoEdit.$el.find('.save-button').click()
                requestSent = JSON.parse(requests[requests.length - 1].requestBody)
                expect(requestSent.push_notification_selected).toEqual(false)

		# Check that analytics send push_notification info
                analytics_payload = window.analytics.track.calls.first().args[1]
                expect(analytics_payload).toEqual(jasmine.objectContaining({'push_notification_selected': false}))

        describe "Course Handouts", ->
            handoutsTemplate = readFixtures('course_info_handouts.underscore')

            beforeEach ->
                setFixtures($("<script>", {id: "course_info_handouts-tpl", type: "text/template"}).text(handoutsTemplate))
                appendSetFixtures courseInfoPage

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

            it "does not rewrite links on save", ->
                requests = AjaxHelpers["requests"](this)

                # Enter something in the handouts section, verifying that the model is saved
                # when "Save" is clicked.
                @handoutsEdit.$el.find('.edit-button').click()
                spyOn(@handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg')
                spyOn(@model, "save").and.callThrough()
                @handoutsEdit.$el.find('.save-button').click()
                expect(@model.save).toHaveBeenCalled()

                contentSaved = JSON.parse(requests[requests.length - 1].requestBody).data
                expect(contentSaved).toEqual('/static/image.jpg')

            it "does rewrite links in initial content", ->
                expect(@handoutsEdit.$preview.html().trim()).toBe('base-asset-url/fromServer.jpg')

            it "does rewrite links after edit", ->
                # Edit handouts and save.
                @handoutsEdit.$el.find('.edit-button').click()
                spyOn(@handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg')
                @handoutsEdit.$el.find('.save-button').click()

                # Verify preview text.
                expect(@handoutsEdit.$preview.html().trim()).toBe('base-asset-url/image.jpg')

            it "shows static links in edit mode", ->
                # Click edit and verify CodeMirror contents.
                @handoutsEdit.$el.find('.edit-button').click()
                expect(@handoutsEdit.$codeMirror.getValue().trim()).toEqual('/static/fromServer.jpg')

            it "can open course handouts with bad html on edit", ->
                # Enter some bad html in handouts section, verifying that the
                # model/handoutform opens when "Edit" is clicked

                @model = new ModuleInfo({
                    id: 'handouts-id',
                    data: '<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>'
                })
                @handoutsEdit = new CourseInfoHandoutsView({
                    el: $('#course-handouts-view'),
                    model: @model,
                    base_asset_url: 'base-asset-url/'
                });
                @handoutsEdit.render()

                expect($('.edit-handouts-form').is(':hidden')).toEqual(true)
                @handoutsEdit.$el.find('.edit-button').click()
                expect(@handoutsEdit.$codeMirror.getValue()).toEqual('<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>')
                expect($('.edit-handouts-form').is(':hidden')).toEqual(false)
