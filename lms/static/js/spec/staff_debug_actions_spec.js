define(['backbone', 'jquery', 'js/staff_debug_actions'],
    function (Backbone, $) {

        describe('StaffDebugActions', function () {
            var location = 'i4x://edX/Open_DemoX/edx_demo_course/problem/test_loc';
            var locationName = 'test_loc';
            var fixture_id = 'sd_fu_' + locationName;
            var fixture = $('<input>', { id: fixture_id, placeholder: "userman" });

            describe('get_url ', function () {
                it('defines url to courseware ajax entry point', function () {
                    spyOn(StaffDebug, "get_current_url").andReturn("/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff");
                    expect(StaffDebug.get_url('rescore_problem')).toBe('/courses/edX/Open_DemoX/edx_demo_course/instructor/api/rescore_problem');
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
            });
            describe('reset', function () {
                it('makes an ajax call with the expected parameters', function () {
                    $('body').append(fixture);

                    spyOn($, 'ajax');
                    StaffDebug.reset(locationName, location);

                    expect($.ajax.mostRecentCall.args[0]['type']).toEqual('GET');
                    expect($.ajax.mostRecentCall.args[0]['data']).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': false
                    });
                    expect($.ajax.mostRecentCall.args[0]['url']).toEqual(
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

                    expect($.ajax.mostRecentCall.args[0]['type']).toEqual('GET');
                    expect($.ajax.mostRecentCall.args[0]['data']).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': true
                    });
                    expect($.ajax.mostRecentCall.args[0]['url']).toEqual(
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

                    expect($.ajax.mostRecentCall.args[0]['type']).toEqual('GET');
                    expect($.ajax.mostRecentCall.args[0]['data']).toEqual({
                        'problem_to_reset': location,
                        'unique_student_identifier': 'userman',
                        'delete_module': false
                    });
                    expect($.ajax.mostRecentCall.args[0]['url']).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + fixture_id).remove();
                });
            });
        });
    });