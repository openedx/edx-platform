define(["coffee/src/views/unit", "js/models/module_info", "js/spec_helpers/create_sinon", "js/views/feedback_notification",
    "jasmine-stealth"],
    function (UnitEditView, ModuleModel, create_sinon, NotificationView) {
        var verifyJSON = function (requests, json) {
            var request = requests[requests.length - 1];
            expect(request.url).toEqual("/xblock/");
            expect(request.method).toEqual("POST");
            // There was a problem with order of returned parameters in strings.
            // Changed to compare objects instead strings.
            expect(JSON.parse(request.requestBody)).toEqual(JSON.parse(json));
        };

        var verifyComponents = function (unit, locators) {
            var components = unit.$(".component");
            expect(components.length).toBe(locators.length);
            for (var i=0; i < locators.length; i++) {
                expect($(components[i]).data('locator')).toBe(locators[i]);
            }
        };

        var verifyNotification = function (notificationSpy, text, requests) {
            expect(notificationSpy.constructor).toHaveBeenCalled();
            expect(notificationSpy.show).toHaveBeenCalled();
            expect(notificationSpy.hide).not.toHaveBeenCalled();
            var options = notificationSpy.constructor.mostRecentCall.args[0];
            expect(options.title).toMatch(text);
            create_sinon.respondWithJson(requests, {"locator": "new_item"});
            expect(notificationSpy.hide).toHaveBeenCalled();
        };

        describe('duplicateComponent ', function () {
            var duplicateFixture =
                '<div class="main-wrapper edit-state-draft" data-locator="unit_locator"> \
                  <ol class="components"> \
                    <li class="component" data-locator="loc_1"> \
                      <div class="wrapper wrapper-component-editor"/> \
                      <ul class="component-actions"> \
                        <a href="#" data-tooltip="Duplicate" class="duplicate-button action-button"><i class="icon-copy"></i><span class="sr"></span>Duplicate</span></a> \
                      </ul> \
                    </li> \
                    <li class="component" data-locator="loc_2"> \
                      <div class="wrapper wrapper-component-editor"/> \
                      <ul class="component-actions"> \
                        <a href="#" data-tooltip="Duplicate" class="duplicate-button action-button"><i class="icon-copy"></i><span class="sr"></span>Duplicate</span></a> \
                      </ul> \
                    </li> \
                  </ol> \
                </div>';

            var unit;
            var clickDuplicate = function (index) {
                unit.$(".duplicate-button")[index].click();
            };
            beforeEach(function () {
                setFixtures(duplicateFixture);
                unit = new UnitEditView({
                    el: $('.main-wrapper'),
                    model: new ModuleModel({
                        id: 'unit_locator',
                        state: 'draft'
                    })
                });
            });

            it('sends the correct JSON to the server', function () {
                var requests = create_sinon.requests(this);
                clickDuplicate(0);
                verifyJSON(requests, '{"duplicate_source_locator":"loc_1","parent_locator":"unit_locator"}');
            });

            it('inserts duplicated component immediately after source upon success', function () {
                var requests = create_sinon.requests(this);
                clickDuplicate(0);
                create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                verifyComponents(unit, ['loc_1', 'duplicated_item', 'loc_2']);
            });

            it('inserts duplicated component at end if source at end', function () {
                var requests = create_sinon.requests(this);
                clickDuplicate(1);
                create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                verifyComponents(unit, ['loc_1', 'loc_2', 'duplicated_item']);
            });

            it('shows a notification while duplicating', function () {
                var notificationSpy = spyOnConstructor(NotificationView, "Mini", ["show", "hide"]);
                notificationSpy.show.andReturn(notificationSpy);

                var requests = create_sinon.requests(this);
                clickDuplicate(0);
                verifyNotification(notificationSpy, /Duplicating/, requests);
            });

            it('does not insert duplicated component upon failure', function () {
                var server = create_sinon.server(500, this);
                clickDuplicate(0);
                server.respond();
                verifyComponents(unit, ['loc_1', 'loc_2']);
            });
        });
        describe('saveNewComponent ', function () {
            var newComponentFixture =
                '<div class="main-wrapper edit-state-draft" data-locator="unit_locator"> \
                  <ol class="components"> \
                    <li class="component" data-locator="loc_1"> \
                      <div class="wrapper wrapper-component-editor"/> \
                    </li> \
                    <li class="component" data-locator="loc_2"> \
                      <div class="wrapper wrapper-component-editor"/> \
                    </li> \
                    <li class="new-component-item adding"> \
                      <div class="new-component"> \
                        <ul class="new-component-type"> \
                          <li> \
                            <a href="#" class="single-template" data-type="discussion" data-category="discussion"/> \
                          </li> \
                        </ul> \
                      </div> \
                    </li> \
                  </ol> \
                </div>';

            var unit;
            var clickNewComponent = function () {
                unit.$(".new-component .new-component-type a.single-template").click();
            };
            beforeEach(function () {
                setFixtures(newComponentFixture);
                unit = new UnitEditView({
                    el: $('.main-wrapper'),
                    model: new ModuleModel({
                        id: 'unit_locator',
                        state: 'draft'
                    })
                });
            });
            it('sends the correct JSON to the server', function () {
                var requests = create_sinon.requests(this);
                clickNewComponent();
                verifyJSON(requests, '{"category":"discussion","type":"discussion","parent_locator":"unit_locator"}');
            });

            it('inserts new component at end', function () {
                var requests = create_sinon.requests(this);
                clickNewComponent();
                create_sinon.respondWithJson(requests, {"locator": "new_item"});
                verifyComponents(unit, ['loc_1', 'loc_2', 'new_item']);
            });

            it('shows a notification while creating', function () {
                var notificationSpy = spyOnConstructor(NotificationView, "Mini", ["show", "hide"]);
                notificationSpy.show.andReturn(notificationSpy);
                var requests = create_sinon.requests(this);
                clickNewComponent();
                verifyNotification(notificationSpy, /Adding/, requests);
            });

            it('does not insert duplicated component upon failure', function () {
                var server = create_sinon.server(500, this);
                clickNewComponent();
                server.respond();
                verifyComponents(unit, ['loc_1', 'loc_2']);
            });
        });
    }
);
