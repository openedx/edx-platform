define([
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/ccx/collection/schedule_collection',
        'js/ccx/view/ccx_schedule'
    ],
    function ($, _, AjaxHelpers, ScheduleCollection, ScheduleView) {
        'use strict';
        describe("edx.ccx.schedule.ScheduleView", function () {
            var save_url = 'save_ccx';
            var view = null;
            var data;

            beforeEach(function () {
                loadFixtures("js/fixtures/ccx/schedule.html");
                $.fn.leanModal = function () {
                    return true;
                };

                data = [{
                    'category': 'chapter',
                    'display_name': 'Introduction',
                    'due': null,
                    'start': null,
                    'location': 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b',
                    'hidden': true,
                    'children': [
                        {
                            "category": "sequential",
                            "display_name": "Demo Course Overview",
                            "due": null,
                            "start": null,
                            "location": "i4x://edX/DemoX/sequential/edx_introduction",
                            "hidden": true,
                            "children": [
                                {
                                    "category": "vertical",
                                    "display_name": "Introduction: Video and Sequences",
                                    "due": null,
                                    "start": null,
                                    "location": "i4x://edX/DemoX/vertical/vertical_0270f6de40fc",
                                    "hidden": true
                                }
                            ]
                        }
                    ]
                }];
                var scheduleCollection = new ScheduleCollection(data);
                view = new ScheduleView({
                    el: $("#ccx-schedule-container"),
                    saveCCXScheduleUrl: save_url,
                    collection: scheduleCollection
                });
                view.render();
            });

            it("verifies correct view setup", function () {
                expect(view.scheduleRightContainer.chapters).toEqual(data);
                expect(view.scheduleTreeView.chapters).toEqual([]);
            });

            it("finds a unit", function () {
                var unit = view.collection.findUnit(
                    view.collection.toJSON(), 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                expect(unit).toEqual(data[0]);
            });

            it("hides a unit", function () {
                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                unit.hidden = false;
                view.collection.hide(unit);
                expect(unit.hidden).toBe(true);
            });

            it("shows a unit", function () {
                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                view.collection.show(unit);
                expect(unit.hidden).toBe(false);
            });

            it("make unit visible", function () {
                view.collection.hideAllUnitFromScheduleTree();
                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );

                expect(unit.hidden).toBe(true);

                view.collection.showUnitInScheduleTree(
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b',
                    undefined,
                    undefined,
                    unit.start,
                    unit.due
                );

                unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );

                expect(unit.hidden).toBe(false);
            });

            it("adds all units to schedule", function () {
                expect(view.scheduleTreeView.chapters).toEqual([]);
                expect(view.scheduleRightContainer.chapters.length).toEqual(1);
                $('#add-all').click();
                expect(view.scheduleTreeView.chapters.length).toEqual(1);
                expect(view.scheduleRightContainer.chapters).toEqual([]);
            });

            it("selects a chapter and adds units to dropdown", function () {
                expect(view.$("select#ccx_sequential").children('option').length).toEqual(0);
                view.$("select#ccx_chapter").change();
                expect(view.$("select#ccx_sequential").prop('disabled')).toEqual(true);
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();
                expect(view.$("select#ccx_chapter").val()).toEqual(val);
                expect(view.$("select#ccx_chapter").prop('disabled')).toEqual(false);
                expect(view.$("select#ccx_chapter").children('option').length).toEqual(2);
            });

            it("selects a unit and adds sections to dropdown", function () {
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();
                expect(view.$("select#ccx_vertical").children('option').length).toEqual(0);
                view.$("select#ccx_sequential").change();
                expect(view.$("select#ccx_vertical").prop('disabled')).toEqual(true);
                val = "i4x://edX/DemoX/sequential/edx_introduction";
                view.$("select#ccx_sequential").val(val);
                view.$("select#ccx_sequential").change();
                expect(view.$("select#ccx_sequential").val()).toEqual(val);
                expect(view.$("select#ccx_vertical").prop('disabled')).toEqual(false);
                expect(view.$("select#ccx_vertical").children('option').length).toEqual(2);
            });

            it("selects a section", function () {
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();
                val = "i4x://edX/DemoX/sequential/edx_introduction";
                view.$("select#ccx_sequential").val(val);
                view.$("select#ccx_sequential").change();
                val = "i4x://edX/DemoX/vertical/vertical_0270f6de40fc";
                view.$("select#ccx_vertical").val(val);
                view.$("select#ccx_vertical").change();
                expect(view.$("select#ccx_vertical").val()).toEqual(val);
            });

            it("adds a unit", function () {
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();

                val = "i4x://edX/DemoX/sequential/edx_introduction";
                view.$("select#ccx_sequential").val(val);
                view.$("select#ccx_sequential").change();

                val = "i4x://edX/DemoX/vertical/vertical_0270f6de40fc";
                view.$("select#ccx_vertical").val(val);
                view.$("select#ccx_vertical").change();

                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );

                view.$('form#add-unit input[name=start_date]').val('2015-12-12');
                view.$('form#add-unit input[name=start_time]').val('10:00');
                view.$('form#add-unit input[name=due_date]').val('2015-12-12');
                view.$('form#add-unit input[name=due_time]').val('10:30');
                expect(unit.hidden).toBe(true);
                $('#add-unit-button').click();
                unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                expect(unit.hidden).toBe(false);
            });

            it("add unit when start date is greater the due date", function () {
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();
                val = "i4x://edX/DemoX/sequential/edx_introduction";
                view.$("select#ccx_sequential").val(val);
                view.$("select#ccx_sequential").change();
                val = "i4x://edX/DemoX/vertical/vertical_0270f6de40fc";
                view.$("select#ccx_vertical").val(val);
                view.$("select#ccx_vertical").change();
                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                // start date is before due date
                view.$('form#add-unit input[name=start_date]').val('2015-11-13');
                view.$('form#add-unit input[name=start_time]').val('10:45');
                view.$('form#add-unit input[name=due_date]').val('2015-11-12');
                view.$('form#add-unit input[name=due_time]').val('10:00');

                expect(unit.hidden).toBe(true);
                $('#add-unit-button').click();
                // Assert unit is not added to schedule
                expect(unit.hidden).toBe(true);
            });

            it("add unit when start date is missing", function () {
                var val = 'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b';
                view.$("select#ccx_chapter").val(val);
                view.$("select#ccx_chapter").change();
                val = "i4x://edX/DemoX/sequential/edx_introduction";
                view.$("select#ccx_sequential").val(val);
                view.$("select#ccx_sequential").change();
                val = "i4x://edX/DemoX/vertical/vertical_0270f6de40fc";
                view.$("select#ccx_vertical").val(val);
                view.$("select#ccx_vertical").change();
                var unit = view.collection.findUnit(
                    view.collection.toJSON(),
                    'i4x://edX/DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b'
                );
                // start date is missing
                view.$('form#add-unit input[name=start_date]').val('');
                view.$('form#add-unit input[name=start_time]').val('');
                view.$('form#add-unit input[name=due_date]').val('2015-12-12');
                view.$('form#add-unit input[name=due_time]').val('10:00');

                expect(unit.hidden).toBe(true);
                $('#add-unit-button').click();
                // Assert unit is not added to schedule
                expect(unit.hidden).toBe(true);
            });

            it("gets a datetime string from date and time fields", function () {
                view.$('form#add-unit input[name=start_date]').val('2015-12-12');
                view.$('form#add-unit input[name=start_time]').val('10:45');
                expect($('form#add-unit input[name=start_date]')).toHaveValue('2015-12-12');
                expect($('form#add-unit input[name=start_time]')).toHaveValue('10:45');
            });

            it("sets date and time fields from datetime string", function () {
                $('form#add-unit input[name=start_date]').val('2015-12-12');
                $('form#add-unit input[name=start_time]').val('10:45');
                var datetime = view.scheduleRightContainer.getDateTime('start');
                expect(datetime).toBe('2015-12-12 10:45');
            });

            it("saves schedule changes", function () {
                var requests = AjaxHelpers.requests(this);
                view.saveSchedule();
                expect(requests.length).toEqual(1);
                AjaxHelpers.expectJsonRequest(
                    requests,
                    'POST',
                    'save_ccx',
                    view.collection.toJSON()
                );
                AjaxHelpers.respondWithJson(requests, {
                    data: view.collection.toJSON()
                });
                expect($('#ajax-error')).toHaveCss({display: 'none'});
            });

            it("displays an error if the sync fails", function () {
                var requests = AjaxHelpers.requests(this);
                view.saveSchedule();
                requests[0].respond(500);
                expect($('#ajax-error')).toHaveCss({display: 'block'});
            });
        });
    }
);
