define(["js/models/textbook", "js/models/chapter", "js/collections/chapter", "js/models/course",
    "js/collections/textbook", "js/views/show_textbook", "js/views/edit_textbook", "js/views/list_textbooks",
    "js/views/edit_chapter", "common/js/components/views/feedback_prompt",
    "common/js/components/views/feedback_notification", "common/js/components/utils/view_utils",
    "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers",
    "js/spec_helpers/modal_helpers"],
    function(Textbook, Chapter, ChapterSet, Course, TextbookSet, ShowTextbook, EditTextbook, ListTextbooks, EditChapter,
        Prompt, Notification, ViewUtils, AjaxHelpers, modal_helpers) {

        describe("ShowTextbook", function() {
            const tpl = readFixtures('show-textbook.underscore');

            beforeEach(function() {
                setFixtures($("<script>", {id: "show-textbook-tpl", type: "text/template"}).text(tpl));
                appendSetFixtures(sandbox({id: "page-notification"}));
                appendSetFixtures(sandbox({id: "page-prompt"}));
                this.model = new Textbook({name: "Life Sciences", id: "0life-sciences"});
                spyOn(this.model, "destroy").and.callThrough();
                this.collection = new TextbookSet([this.model]);
                this.view = new ShowTextbook({model: this.model});

                this.promptSpies = jasmine.stealth.spyOnConstructor(Prompt, "Warning", ["show", "hide"]);
                this.promptSpies.show.and.returnValue(this.promptSpies);
                window.course = new Course({
                    id: "5",
                    name: "Course Name",
                    url_name: "course_name",
                    org: "course_org",
                    num: "course_num",
                    revision: "course_rev"
                });
            });

            afterEach(() => {
                delete window.course;
                jasmine.stealth.clearSpies();
            });

            describe("Basic", function() {
                it("should render properly", function() {
                    this.view.render();
                    expect(this.view.$el).toContainText("Life Sciences");
                });

                it("should set the 'editing' property on the model when the edit button is clicked", function() {
                    this.view.render().$(".edit").click();
                    expect(this.model.get("editing")).toBeTruthy();
                });

                it("should pop a delete confirmation when the delete button is clicked", function() {
                    this.view.render().$(".delete").click();
                    expect(this.promptSpies.constructor).toHaveBeenCalled();
                    const ctorOptions = this.promptSpies.constructor.calls.mostRecent().args[0];
                    expect(ctorOptions.title).toMatch(/Life Sciences/);
                    // hasn't actually been removed
                    expect(this.model.destroy).not.toHaveBeenCalled();
                    expect(this.collection).toContain(this.model);
                });

                it("should show chapters appropriately", function() {
                    this.model.get("chapters").add([{}, {}, {}]);
                    this.model.set('showChapters', false);
                    this.view.render().$(".show-chapters").click();
                    expect(this.model.get('showChapters')).toBeTruthy();
                });

                it("should hide chapters appropriately", function() {
                    this.model.get("chapters").add([{}, {}, {}]);
                    this.model.set('showChapters', true);
                    this.view.render().$(".hide-chapters").click();
                    expect(this.model.get('showChapters')).toBeFalsy();
                });
            });

            describe("AJAX", function() {
                beforeEach(function() {
                    this.savingSpies = jasmine.stealth.spyOnConstructor(Notification, "Mini",
                        ["show", "hide"]);
                    this.savingSpies.show.and.returnValue(this.savingSpies);
                    CMS.URL.TEXTBOOKS = "/textbooks";
                });

                afterEach(() => delete CMS.URL.TEXTBOOKS);

                it("should destroy itself on confirmation", function() {
                    const requests = AjaxHelpers["requests"](this);

                    this.view.render().$(".delete").click();
                    const ctorOptions = this.promptSpies.constructor.calls.mostRecent().args[0];
                    // run the primary function to indicate confirmation
                    ctorOptions.actions.primary.click(this.promptSpies);
                    // AJAX request has been sent, but not yet returned
                    expect(this.model.destroy).toHaveBeenCalled();
                    expect(requests.length).toEqual(1);
                    expect(this.savingSpies.constructor).toHaveBeenCalled();
                    expect(this.savingSpies.show).toHaveBeenCalled();
                    expect(this.savingSpies.hide).not.toHaveBeenCalled();
                    const savingOptions = this.savingSpies.constructor.calls.mostRecent().args[0];
                    expect(savingOptions.title).toMatch(/Deleting/);
                    // return a success response
                    requests[0].respond(204);
                    expect(this.savingSpies.hide).toHaveBeenCalled();
                    expect(this.collection.contains(this.model)).toBeFalsy();
                });
            });
        });

        describe("EditTextbook", () =>
            describe("Basic", function() {
                const tpl = readFixtures('edit-textbook.underscore');

                beforeEach(function() {
                    setFixtures($("<script>", {id: "edit-textbook-tpl", type: "text/template"}).text(tpl));
                    appendSetFixtures(sandbox({id: "page-notification"}));
                    appendSetFixtures(sandbox({id: "page-prompt"}));
                    this.model = new Textbook({name: "Life Sciences", editing: true});
                    spyOn(this.model, 'save');
                    this.collection = new TextbookSet();
                    this.collection.add(this.model);
                    this.view = new EditTextbook({model: this.model});
                    spyOn(this.view, 'render').and.callThrough();
                });

                it("should render properly", function() {
                    this.view.render();
                    expect(this.view.$("input[name=textbook-name]").val()).toEqual("Life Sciences");
                });

                it("should allow you to create new empty chapters", function() {
                    this.view.render();
                    const numChapters = this.model.get("chapters").length;
                    this.view.$(".action-add-chapter").click();
                    expect(this.model.get("chapters").length).toEqual(numChapters+1);
                    expect(this.model.get("chapters").last().isEmpty()).toBeTruthy();
                });

                it("should save properly", function() {
                    this.view.render();
                    this.view.$("input[name=textbook-name]").val("starfish");
                    this.view.$("input[name=chapter1-name]").val("wallflower");
                    this.view.$("input[name=chapter1-asset-path]").val("foobar");
                    this.view.$("form").submit();
                    expect(this.model.get("name")).toEqual("starfish");
                    const chapter = this.model.get("chapters").first();
                    expect(chapter.get("name")).toEqual("wallflower");
                    expect(chapter.get("asset_path")).toEqual("foobar");
                    expect(this.model.save).toHaveBeenCalled();
                });

                it("should not save on invalid", function() {
                    this.view.render();
                    this.view.$("input[name=textbook-name]").val("");
                    this.view.$("input[name=chapter1-asset-path]").val("foobar.pdf");
                    this.view.$("form").submit();
                    expect(this.model.validationError).toBeTruthy();
                    expect(this.model.save).not.toHaveBeenCalled();
                });

                it("does not save on cancel", function() {
                    this.model.get("chapters").add([{name: "a", asset_path: "b"}]);
                    this.view.render();
                    this.view.$("input[name=textbook-name]").val("starfish");
                    this.view.$("input[name=chapter1-asset-path]").val("foobar.pdf");
                    this.view.$(".action-cancel").click();
                    expect(this.model.get("name")).not.toEqual("starfish");
                    const chapter = this.model.get("chapters").first();
                    expect(chapter.get("asset_path")).not.toEqual("foobar");
                    expect(this.model.save).not.toHaveBeenCalled();
                });

                it("does not re-render on cancel", function() {
                    this.view.render();
                    this.view.$(".action-cancel").click();
                    expect(this.view.render.calls.count()).toEqual(1);
                });

                it("should be possible to correct validation errors", function() {
                    this.view.render();
                    this.view.$("input[name=textbook-name]").val("");
                    this.view.$("input[name=chapter1-asset-path]").val("foobar.pdf");
                    this.view.$("form").submit();
                    expect(this.model.validationError).toBeTruthy();
                    expect(this.model.save).not.toHaveBeenCalled();
                    this.view.$("input[name=textbook-name]").val("starfish");
                    this.view.$("input[name=chapter1-name]").val("foobar");
                    this.view.$("form").submit();
                    expect(this.model.validationError).toBeFalsy();
                    expect(this.model.save).toHaveBeenCalled();
                });

                it("removes all empty chapters on cancel if the model has a non-empty chapter", function() {
                    const chapters = this.model.get("chapters");
                    chapters.at(0).set("name", "non-empty");
                    this.model.setOriginalAttributes();
                    this.view.render();
                    chapters.add([{}, {}, {}]); // add three empty chapters
                    expect(chapters.length).toEqual(4);
                    this.view.$(".action-cancel").click();
                    expect(chapters.length).toEqual(1);
                    expect(chapters.first().get('name')).toEqual("non-empty");
                });

                it("removes all empty chapters on cancel except one if the model has no non-empty chapters", function() {
                    const chapters = this.model.get("chapters");
                    this.view.render();
                    chapters.add([{}, {}, {}]); // add three empty chapters
                    expect(chapters.length).toEqual(4);
                    this.view.$(".action-cancel").click();
                    expect(chapters.length).toEqual(1);
                });
            })
        );

        describe("ListTextbooks", function() {
            const noTextbooksTpl = readFixtures("no-textbooks.underscore");
            const editTextbooktpl = readFixtures('edit-textbook.underscore');

            beforeEach(function() {
                appendSetFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl));
                appendSetFixtures($("<script>", {id: "edit-textbook-tpl", type: "text/template"}).text(editTextbooktpl));
                this.collection = new TextbookSet;
                this.view = new ListTextbooks({collection: this.collection});
                this.view.render();
            });

            it("should scroll to newly added textbook", function() {
                spyOn(ViewUtils, 'setScrollOffset');
                this.view.$(".new-button").click();
                const $sectionEl = this.view.$el.find('section:last');
                expect($sectionEl.length).toEqual(1);
                expect(ViewUtils.setScrollOffset).toHaveBeenCalledWith($sectionEl, 0);
            });

            it("should focus first input element of newly added textbook", function() {
                spyOn(jQuery.fn, 'focus').and.callThrough();
                jasmine.addMatchers({
                    toHaveBeenCalledOnJQueryObject() {
                        return {
                            compare(actual, expected) {
                                return {
                                    pass: actual.calls && actual.calls.mostRecent() &&
                                        (actual.calls.mostRecent().object[0] === expected[0])
                                };
                            }
                        };
                    }});
                this.view.$(".new-button").click();
                const $inputEl = this.view.$el.find('section:last input:first');
                expect($inputEl.length).toEqual(1);
                // testing for element focused seems to be tricky
                // (see http://stackoverflow.com/questions/967096)
                // and the following doesn't seem to work
                //           expect($inputEl).toBeFocused()
                //           expect($inputEl.find(':focus').length).toEqual(1)
                expect(jQuery.fn.focus).toHaveBeenCalledOnJQueryObject($inputEl);
            });

            it("should re-render when new textbook added", function() {
                spyOn(this.view, 'render').and.callThrough();
                this.view.$(".new-button").click();
                expect(this.view.render.calls.count()).toEqual(1);
            });

            it("should remove textbook html section on model.destroy", function() {
                    this.model = new Textbook({name: "Life Sciences", id: "0life-sciences"});
                    this.collection.add(this.model);
                    this.view.render();
                    CMS.URL.TEXTBOOKS = "/textbooks"; // for AJAX
                    expect(this.view.$el.find('section').length).toEqual(1);
                    this.model.destroy();
                    expect(this.view.$el.find('section').length).toEqual(0);
                    delete CMS.URL.TEXTBOOKS;
            });
        });

        //    describe "ListTextbooks", ->
        //        noTextbooksTpl = readFixtures("no-textbooks.underscore")
        //
        //        beforeEach ->
        //            setFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl))
        //            @showSpies = spyOnConstructor("ShowTextbook", ["render"])
        //            @showSpies.render.and.returnValue(@showSpies) # equivalent of `return this`
        //            showEl = $("<li>")
        //            @showSpies.$el = showEl
        //            @showSpies.el = showEl.get(0)
        //            @editSpies = spyOnConstructor("EditTextbook", ["render"])
        //            editEl = $("<li>")
        //            @editSpies.render.and.returnValue(@editSpies)
        //            @editSpies.$el = editEl
        //            @editSpies.el= editEl.get(0)
        //
        //            @collection = new TextbookSet
        //            @view = new ListTextbooks({collection: @collection})
        //            @view.render()
        //
        //        it "should render the empty template if there are no textbooks", ->
        //            expect(@view.$el).toContainText("You haven't added any textbooks to this course yet")
        //            expect(@view.$el).toContain(".new-button")
        //            expect(@showSpies.constructor).not.toHaveBeenCalled()
        //            expect(@editSpies.constructor).not.toHaveBeenCalled()
        //
        //        it "should render ShowTextbook views by default if no textbook is being edited", ->
        //            # add three empty textbooks to the collection
        //            @collection.add([{}, {}, {}])
        //            # reset spies due to re-rendering on collection modification
        //            @showSpies.constructor.reset()
        //            @editSpies.constructor.reset()
        //            # render once and test
        //            @view.render()
        //
        //            expect(@view.$el).not.toContainText(
        //                "You haven't added any textbooks to this course yet")
        //            expect(@showSpies.constructor).toHaveBeenCalled()
        //            expect(@showSpies.constructor.calls.length).toEqual(3);
        //            expect(@editSpies.constructor).not.toHaveBeenCalled()
        //
        //        it "should render an EditTextbook view for a textbook being edited", ->
        //            # add three empty textbooks to the collection: the first and third
        //            # should be shown, and the second should be edited
        //            @collection.add([{editing: false}, {editing: true}, {editing: false}])
        //            editing = @collection.at(1)
        //            expect(editing.get("editing")).toBeTruthy()
        //            # reset spies
        //            @showSpies.constructor.reset()
        //            @editSpies.constructor.reset()
        //            # render once and test
        //            @view.render()
        //
        //            expect(@showSpies.constructor).toHaveBeenCalled()
        //            expect(@showSpies.constructor.calls.length).toEqual(2)
        //            expect(@showSpies.constructor).not.toHaveBeenCalledWith({model: editing})
        //            expect(@editSpies.constructor).toHaveBeenCalled()
        //            expect(@editSpies.constructor.calls.length).toEqual(1)
        //            expect(@editSpies.constructor).toHaveBeenCalledWith({model: editing})
        //
        //        it "should add a new textbook when the new-button is clicked", ->
        //            # reset spies
        //            @showSpies.constructor.reset()
        //            @editSpies.constructor.reset()
        //            # test
        //            @view.$(".new-button").click()
        //
        //            expect(@collection.length).toEqual(1)
        //            expect(@view.$el).toContain(@editSpies.$el)
        //            expect(@view.$el).not.toContain(@showSpies.$el)


        describe("EditChapter", function() {
            beforeEach(function() {
                modal_helpers.installModalTemplates();
                this.model = new Chapter({
                    name: "Chapter 1",
                    asset_path: "/ch1.pdf"
                });
                this.collection = new ChapterSet();
                this.collection.add(this.model);
                this.view = new EditChapter({model: this.model});
                spyOn(this.view, "remove").and.callThrough();
                CMS.URL.UPLOAD_ASSET = "/upload";
                window.course = new Course({name: "abcde"});
            });

            afterEach(function() {
                delete CMS.URL.UPLOAD_ASSET;
                delete window.course;
            });

            it("can render", function() {
                this.view.render();
                expect(this.view.$("input.chapter-name").val()).toEqual("Chapter 1");
                expect(this.view.$("input.chapter-asset-path").val()).toEqual("/ch1.pdf");
            });

            it("can delete itself", function() {
                this.view.render().$(".action-close").click();
                expect(this.collection.length).toEqual(0);
                expect(this.view.remove).toHaveBeenCalled();
            });

            //        it "can open an upload dialog", ->
            //            uploadSpies = spyOnConstructor("UploadDialog", ["show", "el"])
            //            uploadSpies.show.and.returnValue(uploadSpies)
            //
            //            @view.render().$(".action-upload").click()
            //            ctorOptions = uploadSpies.constructor.calls.mostRecent().args[0]
            //            expect(ctorOptions.model.get('title')).toMatch(/abcde/)
            //            expect(typeof ctorOptions.onSuccess).toBe('function')
            //            expect(uploadSpies.show).toHaveBeenCalled()

            // Disabling because this test does not close the modal dialog. This can cause
            // tests that run after it to fail (see STUD-1963).
            xit("saves content when opening upload dialog", function() {
                this.view.render();
                this.view.$("input.chapter-name").val("rainbows");
                this.view.$("input.chapter-asset-path").val("unicorns");
                this.view.$(".action-upload").click();
                expect(this.model.get("name")).toEqual("rainbows");
                expect(this.model.get("asset_path")).toEqual("unicorns");
            });
        });
});
