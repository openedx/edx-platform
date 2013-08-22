courseInfoPage = """
                 <div class="course-info-wrapper">
                 <div class="main-column window">
                 <article class="course-updates" id="course-update-view">
                 <ol class="update-list" id="course-update-list"></ol>
                 </article>
                 </div>
                 <div class="sidebar window course-handouts" id="course-handouts-view"></div>
                 </div>
                 """

commonSetup = () ->
    window.analytics = jasmine.createSpyObj('analytics', ['track'])
    window.course_location_analytics = jasmine.createSpy()
    window.courseUpdatesXhr = sinon.useFakeXMLHttpRequest()
    requests = []
    window.courseUpdatesXhr.onCreate = (xhr) -> requests.push(xhr)
    return requests

commonCleanup = () ->
    window.courseUpdatesXhr.restore()
    delete window.analytics
    delete window.course_location_analytics

describe "Course Updates", ->
    courseInfoTemplate = readFixtures('course_info_update.underscore')

    beforeEach ->
        setFixtures($("<script>", {id: "course_info_update-tpl", type: "text/template"}).text(courseInfoTemplate))
        appendSetFixtures courseInfoPage

        @collection = new CMS.Models.CourseUpdateCollection()
        @courseInfoEdit = new CMS.Views.ClassInfoUpdateView({
            el: $('.course-updates'),
            collection: @collection,
            base_asset_url : 'base-asset-url/'
        })

        @courseInfoEdit.render()

        @event = {
            preventDefault : () -> 'no op'
        }

        @createNewUpdate = () ->
            # Edit button is not in the template under test (it is in parent HTML).
            # Therefore call onNew directly.
            @courseInfoEdit.onNew(@event)
            spyOn(@courseInfoEdit.$codeMirror, 'getValue').andReturn('/static/image.jpg')
            @courseInfoEdit.$el.find('.save-button').click()

        @requests = commonSetup()

    afterEach ->
        commonCleanup()

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
        contentSaved = JSON.parse(this.requests[0].requestBody).content
        expect(contentSaved).toEqual('/static/image.jpg')

    it "does rewrite links for preview", ->
        # Create a new update.
        @createNewUpdate()

        # Verify the link is rewritten for preview purposes.
        previewContents = @courseInfoEdit.$el.find('.update-contents').html()
        expect(previewContents).toEqual('base-asset-url/image.jpg')

    it "shows static links in edit mode", ->
        @createNewUpdate()

        # Click edit and verify CodeMirror contents.
        @courseInfoEdit.$el.find('.edit-button').click()
        expect(@courseInfoEdit.$codeMirror.getValue()).toEqual('/static/image.jpg')


describe "Course Handouts", ->
    handoutsTemplate = readFixtures('course_info_handouts.underscore')

    beforeEach ->
        setFixtures($("<script>", {id: "course_info_handouts-tpl", type: "text/template"}).text(handoutsTemplate))
        appendSetFixtures courseInfoPage

        @model = new CMS.Models.ModuleInfo({
            id: 'handouts-id',
            data: '/static/fromServer.jpg'
        })

        @handoutsEdit = new CMS.Views.ClassInfoHandoutsView({
            el: $('#course-handouts-view'),
            model: @model,
            base_asset_url: 'base-asset-url/'
        });

        @handoutsEdit.render()

        @requests = commonSetup()

    afterEach ->
        commonCleanup()

    it "does not rewrite links on save", ->
        # Enter something in the handouts section, verifying that the model is saved
        # when "Save" is clicked.
        @handoutsEdit.$el.find('.edit-button').click()
        spyOn(@handoutsEdit.$codeMirror, 'getValue').andReturn('/static/image.jpg')
        spyOn(@model, "save").andCallThrough()
        @handoutsEdit.$el.find('.save-button').click()
        expect(@model.save).toHaveBeenCalled()

        contentSaved = JSON.parse(this.requests[0].requestBody).data
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

