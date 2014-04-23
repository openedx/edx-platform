describe('StaffDebugActions', function() {
    var loc = 'test_loc';
    var fixture_id = 'sd_fu_' + loc;
    var fixture = $('<input id="' + fixture_id + '" placeholder="userman" />');

    describe('get_url ', function() {
        it('defines url to courseware ajax entry point', function() {
            spyOn(StaffDebug, "get_current_url").andReturn("/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff");
            expect(StaffDebug.get_url('instructor')).toBe('/courses/edX/Open_DemoX/edx_demo_course/instructor');
        });
    });

    describe('get_user', function() {

        it('gets the placeholder username if input field is empty', function() {
            $('body').append(fixture);
            expect(StaffDebug.get_user(loc)).toBe('userman');
            $('#' + fixture_id).remove();
        });
        it('gets a filled in name if there is one', function() {
            $('body').append(fixture);
            $('#' + fixture_id).val('notuserman');
            expect(StaffDebug.get_user(loc)).toBe('notuserman');

            $('#' + fixture_id).val('');
            $('#' + fixture_id).remove();
        });
    });

    describe('reset', function() {
        it('makes an ajax call with the expected parameters', function() {
            $('body').append(fixture);

            spyOn($, 'ajax');
            StaffDebug.reset(loc)

            expect($.ajax.mostRecentCall.args[0]['type']).toEqual('POST');
            expect($.ajax.mostRecentCall.args[0]['data']).toEqual({
                'action': "Reset student's attempts",
                'problem_for_student': loc,
                'unique_student_identifier': 'userman'
            });
            expect($.ajax.mostRecentCall.args[0]['url']).toEqual('/instructor');
            $('#' + fixture_id).remove();
        });
    });
    describe('sdelete', function() {
        it('makes an ajax call with the expected parameters', function() {
            $('body').append(fixture);

            spyOn($, 'ajax');
            StaffDebug.sdelete(loc)

            expect($.ajax.mostRecentCall.args[0]['type']).toEqual('POST');
            expect($.ajax.mostRecentCall.args[0]['data']).toEqual({
                'action': "Delete student state for module",
                'problem_for_student': loc,
                'unique_student_identifier': 'userman'
            });
            expect($.ajax.mostRecentCall.args[0]['url']).toEqual('/instructor');
            $('#' + fixture_id).remove();
        });
    });
});

