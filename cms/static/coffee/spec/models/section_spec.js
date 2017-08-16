/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
define(["js/models/section", "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers", "js/utils/module"], (Section, AjaxHelpers, ModuleUtils) =>
    describe("Section", function() {
        describe("basic", function() {
            beforeEach(function() {
                return this.model = new Section({
                    id: 42,
                    name: "Life, the Universe, and Everything"
                });
            });

            it("should take an id argument", function() {
                return expect(this.model.get("id")).toEqual(42);
            });

            it("should take a name argument", function() {
                return expect(this.model.get("name")).toEqual("Life, the Universe, and Everything");
            });

            it("should have a URL set", function() {
                return expect(this.model.url()).toEqual(ModuleUtils.getUpdateUrl(42));
            });

            return it("should serialize to JSON correctly", function() {
                return expect(this.model.toJSON()).toEqual({
                metadata:
                    {
                    display_name: "Life, the Universe, and Everything"
                    }
                });
            });
        });

        return describe("XHR", function() {
            beforeEach(function() {
                spyOn(Section.prototype, 'showNotification');
                spyOn(Section.prototype, 'hideNotification');
                return this.model = new Section({
                    id: 42,
                    name: "Life, the Universe, and Everything"
                });
            });

            it("show/hide a notification when it saves to the server", function() {
                const server = AjaxHelpers.server([200, {"Content-Type": "application/json"}, "{}"]);

                this.model.save();
                expect(Section.prototype.showNotification).toHaveBeenCalled();
                server.respond();
                return expect(Section.prototype.hideNotification).toHaveBeenCalled();
            });

            return it("don't hide notification when saving fails", function() {
                // this is handled by the global AJAX error handler
                const server = AjaxHelpers.server([500, {"Content-Type": "application/json"}, "{}"]);

                this.model.save();
                server.respond();
                return expect(Section.prototype.hideNotification).not.toHaveBeenCalled();
            });
        });
    })
);
