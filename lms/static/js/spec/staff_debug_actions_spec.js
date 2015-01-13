/* globals define, StaffDebug */
define([
    'backbone', 
    'jquery', 
    'js/staff_debug_actions', 
    'common/js/spec_helpers/ajax_helpers'
    ],
    function (Backbone, $) {
        "use strict";

        describe('StaffDebugActions', function () {
            var location = 'i4x://edX/Open_DemoX/edx_demo_course/problem/test_loc';
            var locationName = 'test_loc';
            var action = {location: location, locationName: locationName};
            var fixture_id = 'sd_fu_' + locationName;
            var fixture = $('<input>', { id: fixture_id, placeholder: "userman" });
            var escapableLocationName = 'test\.\*\+\?\^\:\$\{\}\(\)\|\]\[loc';
            var escapableFixture_id = 'sd_fu_' + escapableLocationName;
            var escapableFixture = $('<input>', {id: escapableFixture_id, placeholder: "userman"});

            describe('get_url ', function () {
                it('defines url to courseware ajax entry point', function () {
                    spyOn(StaffDebug, "get_current_url").andReturn(
                        "/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff"
                    );
                    $('body').append(fixture);
                    var expected_url = '/instructor?unique_student_identifier=userman&problem_to_reset=' +
                        encodeURIComponent(action.location);
                    expect(StaffDebug.get_url(action)).toBe(expected_url);

                    $('#' + fixture_id).remove();
                });
            });

            describe('sanitize_string', function () {
                it('escapes escapable characters in a string', function () {
                    expect(StaffDebug.sanitized_string('.*+?^:${}()|][')).toBe(
                        '\\.\\*\\+\\?\\^\\:\\$\\{\\}\\(\\)\\|\\]\\['
                    );
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
            describe('student_grade_adjustemnts', function () {
                it('makes an ajax call with the expected parameters', function () {
                    $('body').append(fixture);

                    spyOn(StaffDebug, 'goto_student_admin');

                    StaffDebug.student_grade_adjustemnts(locationName, location);

                    var expected_url = StaffDebug.get_url(action) + '#view-student_admin';

                    expect(StaffDebug.goto_student_admin).toHaveBeenCalledWith(expected_url);

                    $('#' + fixture_id).remove();
                });
            });
        });
    });