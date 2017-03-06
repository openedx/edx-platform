define([
    'backbone', 
    'jquery', 
    'js/staff_debug_actions', 
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
    ],
    function (Backbone, $, tmp, AjaxHelpers) {
        'use strict';
        var StaffDebug = window.StaffDebug;

        describe('StaffDebugActions', function () {
            var location = 'i4x://edX/Open_DemoX/edx_demo_course/problem/test_loc';
            var locationName = 'test_loc';
            var fixture_id = 'sd_fu_' + locationName;
            var fixture = $('<input>', { id: fixture_id, placeholder: "userman" });
            var escapableLocationName = 'test\.\*\+\?\^\:\$\{\}\(\)\|\]\[loc';
            var escapableFixture_id = 'sd_fu_' + escapableLocationName;
            var escapableFixture = $('<input>', {id: escapableFixture_id, placeholder: "userman"});
            var esclocationName = 'P2:problem_1';
            var escapableId = 'result_' + esclocationName; 
            var escapableResultArea = $('<div>', {id: escapableId});

            describe('get_url ', function () {
                it('defines url to courseware ajax entry point', function () {
                    spyOn(StaffDebug, "get_current_url")
                      .and.returnValue("/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff");
                    expect(StaffDebug.get_url('rescore_problem'))
                      .toBe('/courses/edX/Open_DemoX/edx_demo_course/instructor/api/rescore_problem');
                });
            });

            describe('sanitize_string', function () {
                it('escapes escapable characters in a string', function () {
                    expect(StaffDebug.sanitized_string('.*+?^:${}()|][')).toBe('\\.\\*\\+\\?\\^\\:\\$\\{\\}\\(\\)\\|\\]\\[');
                });
            });

            describe('get_user', function () {

                it('gets the placeholder username if input field is empty', function () {
                    $('body').append(fixture);
                    expect(StaffDebug.get_user(locationName)).toBe('userman');
                    $('#' + fixture_id).remove();
                });
                it('gets a filled in name if there is one', function () {
                    $('body').append(fixture);
                    $('#' + fixture_id).val('notuserman');
                    expect(StaffDebug.get_user(locationName)).toBe('notuserman');

                    $('#' + fixture_id).val('');
                    $('#' + fixture_id).remove();
                });
                it('gets the placeholder name if the id has escapable characters', function() {
                    $('body').append(escapableFixture);
                    expect(StaffDebug.get_user('test.*+?^:${}()|][loc')).toBe('userman');
                    $("input[id^='sd_fu_']").remove();
                });
            });
            describe('do_idash_action success', function () {
                it('adds a success message to the results element after using an action', function () {
                    $('body').append(escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        success_msg: 'Successfully reset the attempts for user userman',
                    };
                    StaffDebug.do_idash_action(action);
                    AjaxHelpers.respondWithJson(requests, action);
                    expect($('#idash_msg').text()).toBe('Successfully reset the attempts for user userman');
                    $('#result_' + locationName).remove();
                });
            });
            describe('do_idash_action error', function () {
                it('adds a failure message to the results element after using an action', function () {
                    $('body').append(escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        error_msg: 'Failed to reset attempts.',
                    };
                    StaffDebug.do_idash_action(action);
                    AjaxHelpers.respondWithError(requests);
                    expect($('#idash_msg').text()).toBe('Failed to reset attempts. ');
                    $('#result_' + locationName).remove();
                });
            });                    
            describe('reset', function () {
                it('makes an ajax call with the expected parameters', function () {
                    $('body').append(fixture);

                    spyOn($, 'ajax');
                    StaffDebug.reset(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': false
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );
                    $('#' + fixture_id).remove();
                });
            });
            describe('sdelete', function () {
                it('makes an ajax call with the expected parameters', function () {
                    $('body').append(fixture);

                    spyOn($, 'ajax');
                    StaffDebug.sdelete(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': true
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );

                    $('#' + fixture_id).remove();
                });
            });
            describe('rescore', function () {
                it('makes an ajax call with the expected parameters', function () {
                    $('body').append(fixture);

                    spyOn($, 'ajax');
                    StaffDebug.rescore(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': false
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + fixture_id).remove();
                });
            });
        });
    });