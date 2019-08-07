define(["js/views/course_info_handout", "js/views/course_info_update", "js/models/module_info",
        "js/collections/course_update", "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers"],
(CourseInfoHandoutsView, CourseInfoUpdateView, ModuleInfo, CourseUpdateCollection, AjaxHelpers) =>

    describe("Course Updates and Handouts", function() {
        const courseInfoPage = `\
<div class="course-info-wrapper">
<div class="main-column window">
<article class="course-updates" id="course-update-view">
<ol class="update-list" id="course-update-list"></ol>
</article>
</div>
<div class="sidebar window course-handouts" id="course-handouts-view"></div>
</div>
<div class="modal-cover"></div>\
`;

        beforeEach(function() {
            window.analytics = jasmine.createSpyObj('analytics', ['track']);
            window.course_location_analytics = jasmine.createSpy();
        });

        afterEach(function() {
            delete window.analytics;
            delete window.course_location_analytics;
        });

        describe("Course Updates", function() {
            const courseInfoTemplate = readFixtures('course_info_update.underscore');

            beforeEach(function() {
                let cancelEditingUpdate;
                setFixtures($("<script>", {id: "course_info_update-tpl", type: "text/template"}).text(courseInfoTemplate));
                appendSetFixtures(courseInfoPage);

                this.collection = new CourseUpdateCollection();
                this.collection.url = 'course_info_update/';
                this.courseInfoEdit = new CourseInfoUpdateView({
                    el: $('.course-updates'),
                    collection: this.collection,
                    base_asset_url : 'base-asset-url/'
                });

                this.courseInfoEdit.render();

                this.event = {
                    preventDefault() { return 'no op'; }
                };

                this.createNewUpdate = function(text) {
                    // Edit button is not in the template under test (it is in parent HTML).
                    // Therefore call onNew directly.
                    this.courseInfoEdit.onNew(this.event);
                    spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue(text);
                    return this.courseInfoEdit.$el.find('.save-button').click();
                };

                this.cancelNewCourseInfo = function(useCancelButton) {
                    this.courseInfoEdit.onNew(this.event);
                    spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();

                    spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes');
                    const model = this.collection.at(0);
                    spyOn(model, "save").and.callThrough();

                    cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, useCancelButton);

                    expect(this.courseInfoEdit.$modalCover.hide).toHaveBeenCalled();
                    expect(model.save).not.toHaveBeenCalled();
                    const previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                    expect(previewContents).not.toEqual('unsaved changes');
                };

                this.doNotCloseNewCourseInfo = function() {
                    this.courseInfoEdit.onNew(this.event);
                    spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();

                    spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes');
                    const model = this.collection.at(0);
                    spyOn(model, "save").and.callThrough();

                    cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, false);

                    expect(model.save).not.toHaveBeenCalled();
                    expect(this.courseInfoEdit.$modalCover.hide).not.toHaveBeenCalled();
                };

                this.cancelExistingCourseInfo = function(useCancelButton) {
                    this.createNewUpdate('existing update');
                    this.courseInfoEdit.$el.find('.edit-button').click();
                    spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();

                    spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('modification');
                    const model = this.collection.at(0);
                    spyOn(model, "save").and.callThrough();
                    model.id = "saved_to_server";
                    cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, useCancelButton);

                    expect(this.courseInfoEdit.$modalCover.hide).toHaveBeenCalled();
                    expect(model.save).not.toHaveBeenCalled();
                    const previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                    expect(previewContents).toEqual('existing update');
                };

                this.testInvalidDateValue = function(value) {
                    this.courseInfoEdit.onNew(this.event);
                    expect(this.courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(false);
                    this.courseInfoEdit.$el.find('input.date').val(value).trigger("change");
                    expect(this.courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(true);
                    this.courseInfoEdit.$el.find('input.date').val("01/01/16").trigger("change");
                    expect(this.courseInfoEdit.$el.find('.save-button').hasClass("is-disabled")).toEqual(false);
                };

                return cancelEditingUpdate = function(update, modalCover, useCancelButton) {
                    if (useCancelButton) {
                        return update.$el.find('.cancel-button').click();
                    } else {
                        return modalCover.click();
                    }
                };
            });

            it("does send expected data on save", function() {
                const requests = AjaxHelpers["requests"](this);

                // Create a new update, verifying that the model is created
                // in the collection and save is called.
                expect(this.collection.isEmpty()).toBeTruthy();
                this.courseInfoEdit.onNew(this.event);
                expect(this.collection.length).toEqual(1);
                const model = this.collection.at(0);
                spyOn(model, "save").and.callThrough();
                spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');

                // Click the "Save button."
                this.courseInfoEdit.$el.find('.save-button').click();
                expect(model.save).toHaveBeenCalled();

                const requestSent = JSON.parse(requests[requests.length - 1].requestBody);
                // Verify the link is not rewritten when saved.
                expect(requestSent.content).toEqual('/static/image.jpg');

                // Verify that analytics are sent
                expect(window.analytics.track).toHaveBeenCalled();
            });

            it("does rewrite links for preview", function() {
                // Create a new update.
                this.createNewUpdate('/static/image.jpg');

                // Verify the link is rewritten for preview purposes.
                const previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                expect(previewContents).toEqual('base-asset-url/image.jpg');
            });

            it("shows static links in edit mode", function() {
                this.createNewUpdate('/static/image.jpg');

                // Click edit and verify CodeMirror contents.
                this.courseInfoEdit.$el.find('.edit-button').click();
                expect(this.courseInfoEdit.$codeMirror.getValue()).toEqual('/static/image.jpg');
            });

            it("removes newly created course info on cancel", function() {
                this.cancelNewCourseInfo(true);
            });

            it("do not close new course info on click outside modal", function() {
                this.doNotCloseNewCourseInfo();
            });

            it("does not remove existing course info on cancel", function() {
                this.cancelExistingCourseInfo(true);
            });

            it("does not remove existing course info on click outside modal", function() {
                this.cancelExistingCourseInfo(false);
            });

            it("does not allow updates to be saved with an invalid date", function() {
                this.testInvalidDateValue("Marchtober 40, 2048");
            });

            it("does not allow updates to be saved with a blank date", function() {
                this.testInvalidDateValue("");
            });
        });


        describe("Course Handouts", function() {
            const handoutsTemplate = readFixtures('course_info_handouts.underscore');

            beforeEach(function() {
                setFixtures($("<script>", {id: "course_info_handouts-tpl", type: "text/template"}).text(handoutsTemplate));
                appendSetFixtures(courseInfoPage);

                this.model = new ModuleInfo({
                    id: 'handouts-id',
                    data: '/static/fromServer.jpg'
                });

                this.handoutsEdit = new CourseInfoHandoutsView({
                    el: $('#course-handouts-view'),
                    model: this.model,
                    base_asset_url: 'base-asset-url/'
                });

                this.handoutsEdit.render();
            });

            it("saves <ol></ol> when content left empty", function() {
                const requests = AjaxHelpers["requests"](this);

                // Enter empty string in the handouts section, verifying that the model
                // is saved with '<ol></ol>' instead of the empty string
                this.handoutsEdit.$el.find('.edit-button').click();
                spyOn(this.handoutsEdit.$codeMirror, 'getValue').and.returnValue('');
                spyOn(this.model, "save").and.callThrough();
                this.handoutsEdit.$el.find('.save-button').click();
                expect(this.model.save).toHaveBeenCalled();

                const contentSaved = JSON.parse(requests[requests.length - 1].requestBody).data;
                expect(contentSaved).toEqual('<ol></ol>');
            });

            it("does not rewrite links on save", function() {
                const requests = AjaxHelpers["requests"](this);

                // Enter something in the handouts section, verifying that the model is saved
                // when "Save" is clicked.
                this.handoutsEdit.$el.find('.edit-button').click();
                spyOn(this.handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');
                spyOn(this.model, "save").and.callThrough();
                this.handoutsEdit.$el.find('.save-button').click();
                expect(this.model.save).toHaveBeenCalled();

                const contentSaved = JSON.parse(requests[requests.length - 1].requestBody).data;
                expect(contentSaved).toEqual('/static/image.jpg');
            });

            it("does rewrite links in initial content", function() {
                expect(this.handoutsEdit.$preview.html().trim()).toBe('base-asset-url/fromServer.jpg');
            });

            it("does rewrite links after edit", function() {
                // Edit handouts and save.
                this.handoutsEdit.$el.find('.edit-button').click();
                spyOn(this.handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');
                this.handoutsEdit.$el.find('.save-button').click();

                // Verify preview text.
                expect(this.handoutsEdit.$preview.html().trim()).toBe('base-asset-url/image.jpg');
            });

            it("shows static links in edit mode", function() {
                // Click edit and verify CodeMirror contents.
                this.handoutsEdit.$el.find('.edit-button').click();
                expect(this.handoutsEdit.$codeMirror.getValue().trim()).toEqual('/static/fromServer.jpg');
            });

            it("can open course handouts with bad html on edit", function() {
                // Enter some bad html in handouts section, verifying that the
                // model/handoutform opens when "Edit" is clicked

                this.model = new ModuleInfo({
                    id: 'handouts-id',
                    data: '<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>'
                });
                this.handoutsEdit = new CourseInfoHandoutsView({
                    el: $('#course-handouts-view'),
                    model: this.model,
                    base_asset_url: 'base-asset-url/'
                });
                this.handoutsEdit.render();

                expect($('.edit-handouts-form').is(':hidden')).toEqual(true);
                this.handoutsEdit.$el.find('.edit-button').click();
                expect(this.handoutsEdit.$codeMirror.getValue()).toEqual('<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>');
                expect($('.edit-handouts-form').is(':hidden')).toEqual(false);
            });
        });
    })
);
