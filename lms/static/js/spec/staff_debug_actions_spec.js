define([
    'backbone',
    'jquery',
    'js/staff_debug_actions',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
],
    function(Backbone, $, tmp, AjaxHelpers) {
        'use strict';
        var StaffDebug = window.StaffDebug;

        describe('StaffDebugActions', function() {
            var location = 'i4x://edX/Open_DemoX/edx_demo_course/problem/test_loc';
            var locationName = 'test_loc';
            var fixtureID = 'sd_fu_' + locationName;
            var $fixture = $('<input>', {id: fixtureID, placeholder: 'userman'});
            var escapableLocationName = 'test\.\*\+\?\^\:\$\{\}\(\)\|\]\[loc';
            var escapableFixtureID = 'sd_fu_' + escapableLocationName;
            var $escapableFixture = $('<input>', {id: escapableFixtureID, placeholder: 'userman'});
            var esclocationName = 'P2:problem_1';
            var escapableId = 'result_' + esclocationName;
            var escapableResultArea = $('<div>', {id: escapableId});

            describe('getURL ', function() {
                it('defines url to courseware ajax entry point', function() {
                    spyOn(StaffDebug, 'getCurrentUrl')
                      .and.returnValue('/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff');
                    expect(StaffDebug.getURL('rescore_problem'))
                      .toBe('/courses/edX/Open_DemoX/edx_demo_course/instructor/api/rescore_problem');
                });
            });

            describe('sanitizeString', function() {
                it('escapes escapable characters in a string', function() {
                    expect(StaffDebug.sanitizeString('.*+?^:${}()|]['))
                      .toBe('\\.\\*\\+\\?\\^\\:\\$\\{\\}\\(\\)\\|\\]\\[');
                });
            });

            describe('getUser', function() {
                it('gets the placeholder username if input field is empty', function() {
                    $('body').append($fixture);
                    expect(StaffDebug.getUser(locationName)).toBe('userman');
                    $('#' + fixtureID).remove();
                });
                it('gets a filled in name if there is one', function() {
                    $('body').append($fixture);
                    $('#' + fixtureID).val('notuserman');
                    expect(StaffDebug.getUser(locationName)).toBe('notuserman');

                    $('#' + fixtureID).val('');
                    $('#' + fixtureID).remove();
                });
                it('gets the placeholder name if the id has escapable characters', function() {
                    $('body').append($escapableFixture);
                    expect(StaffDebug.getUser('test.*+?^:${}()|][loc')).toBe('userman');
                    $("input[id^='sd_fu_']").remove();
                });
            });
            describe('doInstructorDashAction success', function() {
                it('adds a success message to the results element after using an action', function() {
                    $('body').append(escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        success_msg: 'Successfully reset the attempts for user userman'
                    };
                    StaffDebug.doInstructorDashAction(action);
                    AjaxHelpers.respondWithJson(requests, action);
                    expect($('#idash_msg').text()).toBe('Successfully reset the attempts for user userman');
                    $('#result_' + locationName).remove();
                });
            });
            describe('doInstructorDashAction error', function() {
                it('adds a failure message to the results element after using an action', function() {
                    $('body').append(escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        error_msg: 'Failed to reset attempts for user.'
                    };
                    StaffDebug.doInstructorDashAction(action);
                    AjaxHelpers.respondWithError(requests);
                    expect($('#idash_msg').text()).toBe('Failed to reset attempts for user. ');
                    $('#result_' + locationName).remove();
                });
            });
            describe('reset', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($fixture);

                    spyOn($, 'ajax');
                    StaffDebug.reset(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: false,
                        only_if_higher: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );
                    $('#' + fixtureID).remove();
                });
            });
            describe('deleteStudentState', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($fixture);

                    spyOn($, 'ajax');
                    StaffDebug.deleteStudentState(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: true,
                        only_if_higher: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );

                    $('#' + fixtureID).remove();
                });
            });
            describe('rescore', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($fixture);

                    spyOn($, 'ajax');
                    StaffDebug.rescore(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: undefined,
                        only_if_higher: false
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + fixtureID).remove();
                });
            });
            describe('rescoreIfHigher', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($fixture);

                    spyOn($, 'ajax');
                    StaffDebug.rescoreIfHigher(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: undefined,
                        only_if_higher: true
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + fixtureID).remove();
                });
            });
        });
    });
