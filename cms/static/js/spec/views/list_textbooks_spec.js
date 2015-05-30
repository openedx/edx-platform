define(
    [
        'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'squire',
    ],
function ($, _, AjaxHelpers, Squire) {
    'use strict';
    describe("ListTexbooks", function() {
        var noTextbooksTpl = readFixtures("no-textbooks.underscore");
        var feedbackTpl = readFixtures("system-feedback.underscore");
        var injector;

        var createConstructorSpy = function (name) {
            var spy = jasmine.createSpyObj(name, ['constructor', 'show', 'hide']);
            spy.constructor.andReturn(spy);
            spy.show.andReturn(spy);
            spy.extend = jasmine.createSpy().andReturn(spy.constructor);
            spy.$el = $("<li>");
            spy.el = spy.$el.get(0);

            return spy;
        };

        beforeEach(function() {
            var self = this;
            setFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl));
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl));

            injector = new Squire();
            this.showSpies = createConstructorSpy("showSpy");
            injector.mock("js/views/show_textbook", function () {
                return self.showSpies;
            });
            this.editSpies = createConstructorSpy("editSpies");
            injector.mock("js/views/edit_textbook", function () {
                return self.editSpies;
            });

            runs(function() {
                injector.require([
                    "js/collections/textbook", "js/views/list_textbooks",
                ],
                function(TextbookSet, ListTextbooks) {
                    self.collection = new TextbookSet;
                    self.view = new ListTextbooks({collection: self.collection})
                    self.view.render()
                });
            });

            waitsFor(function() {
                return self.view;
            }, 'ListTextbooks view was not created', 1000);
        });

        afterEach(function () {
            injector.clean();
            injector.remove();
        });

        it("should render the empty template if there are no textbooks", function () {
            expect(this.view.$el).toContainText("You haven't added any textbooks to this course yet")
            expect(this.view.$el).toContain(".new-button")
            expect(this.showSpies.constructor).not.toHaveBeenCalled()
            expect(this.editSpies.constructor).not.toHaveBeenCalled()
        });

        it("should render ShowTextbook views by default if no textbook is being edited", function () {
            // add three empty textbooks to the collection
            this.collection.add([{}, {}, {}])
            // reset spies due to re-rendering on collection modification
            this.showSpies.constructor.reset()
            this.editSpies.constructor.reset()
            // render once and test
            this.view.render()

            expect(this.view.$el).not.toContainText(
                "You haven't added any textbooks to this course yet")
            expect(this.showSpies.constructor).toHaveBeenCalled()
            expect(this.showSpies.constructor.calls.length).toEqual(3);
            expect(this.editSpies.constructor).not.toHaveBeenCalled()
        });

        it("should render an EditTextbook view for a textbook being edited", function () {
            // add three empty textbooks to the collection: the first and third
            // should be shown, and the second should be edited
            this.collection.add([{editing: false}, {editing: true}, {editing: false}])
            editing = this.collection.at(1)
            expect(editing.get("editing")).toBeTruthy()
            // reset spies
            this.showSpies.constructor.reset()
            this.editSpies.constructor.reset()
            // render once and test
            this.view.render()

            expect(this.showSpies.constructor).toHaveBeenCalled()
            expect(this.showSpies.constructor.calls.length).toEqual(2)
            expect(this.showSpies.constructor).not.toHaveBeenCalledWith({model: editing})
            expect(this.editSpies.constructor).toHaveBeenCalled()
            expect(this.editSpies.constructor.calls.length).toEqual(1)
            expect(this.editSpies.constructor).toHaveBeenCalledWith({model: editing})
        });

        it("should add a new textbook when the new-button is clicked", function () {
            // reset spies
            this.showSpies.constructor.reset()
            this.editSpies.constructor.reset()
            // test
            this.view.$(".new-button").click()

            expect(this.collection.length).toEqual(1)
            expect(this.view.$el).toContain(this.editSpies.$el)
            expect(this.view.$el).not.toContain(this.showSpies.$el)
        });
    });
});
