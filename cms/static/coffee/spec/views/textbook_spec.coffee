define ["js/models/textbook", "js/models/chapter", "js/collections/chapter", "js/models/course",
    "js/collections/textbook", "js/views/show_textbook", "js/views/edit_textbook", "js/views/list_textbooks",
    "js/views/edit_chapter", "js/views/feedback_prompt", "js/views/feedback_notification", "js/views/utils/view_utils",
    "common/js/spec_helpers/ajax_helpers", "js/spec_helpers/modal_helpers", "jasmine-stealth"],
(Textbook, Chapter, ChapterSet, Course, TextbookSet, ShowTextbook, EditTextbook, ListTextbooks, EditChapter, Prompt, Notification, ViewUtils, AjaxHelpers, modal_helpers) ->
    feedbackTpl = readFixtures('system-feedback.underscore')

    beforeEach ->
        # remove this when we upgrade jasmine-jquery
        @addMatchers
            toContainText: (text) ->
                trimmedText = $.trim(@actual.text())
                if text and $.isFunction(text.test)
                    return text.test(trimmedText)
                else
                    return trimmedText.indexOf(text) != -1;

    describe "ShowTextbook", ->
        tpl = readFixtures('show-textbook.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "show-textbook-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            appendSetFixtures(sandbox({id: "page-notification"}))
            appendSetFixtures(sandbox({id: "page-prompt"}))
            @model = new Textbook({name: "Life Sciences", id: "0life-sciences"})
            spyOn(@model, "destroy").andCallThrough()
            @collection = new TextbookSet([@model])
            @view = new ShowTextbook({model: @model})

            @promptSpies = spyOnConstructor(Prompt, "Warning", ["show", "hide"])
            @promptSpies.show.andReturn(@promptSpies)
            window.course = new Course({
                id: "5",
                name: "Course Name",
                url_name: "course_name",
                org: "course_org",
                num: "course_num",
                revision: "course_rev"
            });

        afterEach ->
            delete window.course

        describe "Basic", ->
            it "should render properly", ->
                @view.render()
                expect(@view.$el).toContainText("Life Sciences")

            it "should set the 'editing' property on the model when the edit button is clicked", ->
                @view.render().$(".edit").click()
                expect(@model.get("editing")).toBeTruthy()

            it "should pop a delete confirmation when the delete button is clicked", ->
                @view.render().$(".delete").click()
                expect(@promptSpies.constructor).toHaveBeenCalled()
                ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
                expect(ctorOptions.title).toMatch(/Life Sciences/)
                # hasn't actually been removed
                expect(@model.destroy).not.toHaveBeenCalled()
                expect(@collection).toContain(@model)

            it "should show chapters appropriately", ->
                @model.get("chapters").add([{}, {}, {}])
                @model.set('showChapters', false)
                @view.render().$(".show-chapters").click()
                expect(@model.get('showChapters')).toBeTruthy()

            it "should hide chapters appropriately", ->
                @model.get("chapters").add([{}, {}, {}])
                @model.set('showChapters', true)
                @view.render().$(".hide-chapters").click()
                expect(@model.get('showChapters')).toBeFalsy()

        describe "AJAX", ->
            beforeEach ->
                @savingSpies = spyOnConstructor(Notification, "Mini",
                    ["show", "hide"])
                @savingSpies.show.andReturn(@savingSpies)
                CMS.URL.TEXTBOOKS = "/textbooks"

            afterEach ->
                delete CMS.URL.TEXTBOOKS

            it "should destroy itself on confirmation", ->
                requests = AjaxHelpers["requests"](this)

                @view.render().$(".delete").click()
                ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
                # run the primary function to indicate confirmation
                ctorOptions.actions.primary.click(@promptSpies)
                # AJAX request has been sent, but not yet returned
                expect(@model.destroy).toHaveBeenCalled()
                expect(requests.length).toEqual(1)
                expect(@savingSpies.constructor).toHaveBeenCalled()
                expect(@savingSpies.show).toHaveBeenCalled()
                expect(@savingSpies.hide).not.toHaveBeenCalled()
                savingOptions = @savingSpies.constructor.mostRecentCall.args[0]
                expect(savingOptions.title).toMatch(/Deleting/)
                # return a success response
                requests[0].respond(200)
                expect(@savingSpies.hide).toHaveBeenCalled()
                expect(@collection.contains(@model)).toBeFalsy()

    describe "EditTextbook", ->
        describe "Basic", ->
            tpl = readFixtures('edit-textbook.underscore')
            chapterTpl = readFixtures('edit-chapter.underscore')

            beforeEach ->
                setFixtures($("<script>", {id: "edit-textbook-tpl", type: "text/template"}).text(tpl))
                appendSetFixtures($("<script>", {id: "edit-chapter-tpl", type: "text/template"}).text(chapterTpl))
                appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
                appendSetFixtures(sandbox({id: "page-notification"}))
                appendSetFixtures(sandbox({id: "page-prompt"}))
                @model = new Textbook({name: "Life Sciences", editing: true})
                spyOn(@model, 'save')
                @collection = new TextbookSet()
                @collection.add(@model)
                @view = new EditTextbook({model: @model})
                spyOn(@view, 'render').andCallThrough()

            it "should render properly", ->
                @view.render()
                expect(@view.$("input[name=textbook-name]").val()).toEqual("Life Sciences")

            it "should allow you to create new empty chapters", ->
                @view.render()
                numChapters = @model.get("chapters").length
                @view.$(".action-add-chapter").click()
                expect(@model.get("chapters").length).toEqual(numChapters+1)
                expect(@model.get("chapters").last().isEmpty()).toBeTruthy()

            it "should save properly", ->
                @view.render()
                @view.$("input[name=textbook-name]").val("starfish")
                @view.$("input[name=chapter1-name]").val("wallflower")
                @view.$("input[name=chapter1-asset-path]").val("foobar")
                @view.$("form").submit()
                expect(@model.get("name")).toEqual("starfish")
                chapter = @model.get("chapters").first()
                expect(chapter.get("name")).toEqual("wallflower")
                expect(chapter.get("asset_path")).toEqual("foobar")
                expect(@model.save).toHaveBeenCalled()

            it "should not save on invalid", ->
                @view.render()
                @view.$("input[name=textbook-name]").val("")
                @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
                @view.$("form").submit()
                expect(@model.validationError).toBeTruthy()
                expect(@model.save).not.toHaveBeenCalled()

            it "does not save on cancel", ->
                @model.get("chapters").add([{name: "a", asset_path: "b"}])
                @view.render()
                @view.$("input[name=textbook-name]").val("starfish")
                @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
                @view.$(".action-cancel").click()
                expect(@model.get("name")).not.toEqual("starfish")
                chapter = @model.get("chapters").first()
                expect(chapter.get("asset_path")).not.toEqual("foobar")
                expect(@model.save).not.toHaveBeenCalled()

            it "should be possible to correct validation errors", ->
                @view.render()
                @view.$("input[name=textbook-name]").val("")
                @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
                @view.$("form").submit()
                expect(@model.validationError).toBeTruthy()
                expect(@model.save).not.toHaveBeenCalled()
                @view.$("input[name=textbook-name]").val("starfish")
                @view.$("input[name=chapter1-name]").val("foobar")
                @view.$("form").submit()
                expect(@model.validationError).toBeFalsy()
                expect(@model.save).toHaveBeenCalled()

            it "removes all empty chapters on cancel if the model has a non-empty chapter", ->
                chapters = @model.get("chapters")
                chapters.at(0).set("name", "non-empty")
                @model.setOriginalAttributes()
                @view.render()
                chapters.add([{}, {}, {}]) # add three empty chapters
                expect(chapters.length).toEqual(4)
                @view.$(".action-cancel").click()
                expect(chapters.length).toEqual(1)
                expect(chapters.first().get('name')).toEqual("non-empty")

            it "removes all empty chapters on cancel except one if the model has no non-empty chapters", ->
                chapters = @model.get("chapters")
                @view.render()
                chapters.add([{}, {}, {}]) # add three empty chapters
                expect(chapters.length).toEqual(4)
                @view.$(".action-cancel").click()
                expect(chapters.length).toEqual(1)

    describe "ListTextbooks", ->
        noTextbooksTpl = readFixtures("no-textbooks.underscore")
        editTextbooktpl = readFixtures('edit-textbook.underscore')

        beforeEach ->
            appendSetFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl))
            appendSetFixtures($("<script>", {id: "edit-textbook-tpl", type: "text/template"}).text(editTextbooktpl))
            @collection = new TextbookSet
            @view = new ListTextbooks({collection: @collection})
            @view.render()

        it "should scroll to newly added textbook", ->
            spyOn(ViewUtils, 'setScrollOffset')
            @view.$(".new-button").click()
            $sectionEl = @view.$el.find('section:last')
            expect($sectionEl.length).toEqual(1)
            expect(ViewUtils.setScrollOffset).toHaveBeenCalledWith($sectionEl, 0)

        it "should focus first input element of newly added textbook", ->
            spyOn(jQuery.fn, 'focus').andCallThrough()
            @addMatchers
                toHaveBeenCalledOnJQueryObject: (actual, expected) ->
                        pass: actual.calls && actual.calls.mostRecent() && actual.calls.mostRecent().object[0] == expected[0]
            @view.$(".new-button").click()
            $inputEl = @view.$el.find('section:last input:first')
            expect($inputEl.length).toEqual(1)
            # testing for element focused seems to be tricky
            # (see http://stackoverflow.com/questions/967096)
            # and the following doesn't seem to work
#           expect($inputEl).toBeFocused()
#           expect($inputEl.find(':focus').length).toEqual(1)
            expect(jQuery.fn.focus).toHaveBeenCalledOnJQueryObject($inputEl)

#    describe "ListTextbooks", ->
#        noTextbooksTpl = readFixtures("no-textbooks.underscore")
#
#        beforeEach ->
#            setFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl))
#            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
#            @showSpies = spyOnConstructor("ShowTextbook", ["render"])
#            @showSpies.render.andReturn(@showSpies) # equivalent of `return this`
#            showEl = $("<li>")
#            @showSpies.$el = showEl
#            @showSpies.el = showEl.get(0)
#            @editSpies = spyOnConstructor("EditTextbook", ["render"])
#            editEl = $("<li>")
#            @editSpies.render.andReturn(@editSpies)
#            @editSpies.$el = editEl
#            @editSpies.el= editEl.get(0)
#
#            @collection = new TextbookSet
#            @view = new ListTextbooks({collection: @collection})
#            @view.render()
#
#        it "should render the empty template if there are no textbooks", ->
#            expect(@view.$el).toContainText("You haven't added any textbooks to this course yet")
#            expect(@view.$el).toContain(".new-button")
#            expect(@showSpies.constructor).not.toHaveBeenCalled()
#            expect(@editSpies.constructor).not.toHaveBeenCalled()
#
#        it "should render ShowTextbook views by default if no textbook is being edited", ->
#            # add three empty textbooks to the collection
#            @collection.add([{}, {}, {}])
#            # reset spies due to re-rendering on collection modification
#            @showSpies.constructor.reset()
#            @editSpies.constructor.reset()
#            # render once and test
#            @view.render()
#
#            expect(@view.$el).not.toContainText(
#                "You haven't added any textbooks to this course yet")
#            expect(@showSpies.constructor).toHaveBeenCalled()
#            expect(@showSpies.constructor.calls.length).toEqual(3);
#            expect(@editSpies.constructor).not.toHaveBeenCalled()
#
#        it "should render an EditTextbook view for a textbook being edited", ->
#            # add three empty textbooks to the collection: the first and third
#            # should be shown, and the second should be edited
#            @collection.add([{editing: false}, {editing: true}, {editing: false}])
#            editing = @collection.at(1)
#            expect(editing.get("editing")).toBeTruthy()
#            # reset spies
#            @showSpies.constructor.reset()
#            @editSpies.constructor.reset()
#            # render once and test
#            @view.render()
#
#            expect(@showSpies.constructor).toHaveBeenCalled()
#            expect(@showSpies.constructor.calls.length).toEqual(2)
#            expect(@showSpies.constructor).not.toHaveBeenCalledWith({model: editing})
#            expect(@editSpies.constructor).toHaveBeenCalled()
#            expect(@editSpies.constructor.calls.length).toEqual(1)
#            expect(@editSpies.constructor).toHaveBeenCalledWith({model: editing})
#
#        it "should add a new textbook when the new-button is clicked", ->
#            # reset spies
#            @showSpies.constructor.reset()
#            @editSpies.constructor.reset()
#            # test
#            @view.$(".new-button").click()
#
#            expect(@collection.length).toEqual(1)
#            expect(@view.$el).toContain(@editSpies.$el)
#            expect(@view.$el).not.toContain(@showSpies.$el)


    describe "EditChapter", ->
        tpl = readFixtures("edit-chapter.underscore")

        beforeEach ->
            modal_helpers.installModalTemplates()
            appendSetFixtures($("<script>", {id: "edit-chapter-tpl", type: "text/template"}).text(tpl))
            @model = new Chapter
                name: "Chapter 1"
                asset_path: "/ch1.pdf"
            @collection = new ChapterSet()
            @collection.add(@model)
            @view = new EditChapter({model: @model})
            spyOn(@view, "remove").andCallThrough()
            CMS.URL.UPLOAD_ASSET = "/upload"
            window.course = new Course({name: "abcde"})

        afterEach ->
            delete CMS.URL.UPLOAD_ASSET
            delete window.course

        it "can render", ->
            @view.render()
            expect(@view.$("input.chapter-name").val()).toEqual("Chapter 1")
            expect(@view.$("input.chapter-asset-path").val()).toEqual("/ch1.pdf")

        it "can delete itself", ->
            @view.render().$(".action-close").click()
            expect(@collection.length).toEqual(0)
            expect(@view.remove).toHaveBeenCalled()

#        it "can open an upload dialog", ->
#            uploadSpies = spyOnConstructor("UploadDialog", ["show", "el"])
#            uploadSpies.show.andReturn(uploadSpies)
#
#            @view.render().$(".action-upload").click()
#            ctorOptions = uploadSpies.constructor.mostRecentCall.args[0]
#            expect(ctorOptions.model.get('title')).toMatch(/abcde/)
#            expect(typeof ctorOptions.onSuccess).toBe('function')
#            expect(uploadSpies.show).toHaveBeenCalled()

        # Disabling because this test does not close the modal dialog. This can cause
        # tests that run after it to fail (see STUD-1963).
        xit "saves content when opening upload dialog", ->
            @view.render()
            @view.$("input.chapter-name").val("rainbows")
            @view.$("input.chapter-asset-path").val("unicorns")
            @view.$(".action-upload").click()
            expect(@model.get("name")).toEqual("rainbows")
            expect(@model.get("asset_path")).toEqual("unicorns")
