/* globals _ */
// Build StaffDebug object
var StaffDebug = (function() {
    var getURL = function(courseId, action) {
        return '/courses/' + courseId + '/instructor/api/' + action;
    };

    var sanitizeString = function(string) {
        return string.replace(/[.*+?^:${}()|[\]\\]/g, '\\$&');
    };

    var getUser = function(locationName) {
        var sanitizedLocationName = sanitizeString(locationName);
        var uname = $('#sd_fu_' + sanitizedLocationName).val();
        if (uname === '') {
            uname = $('#sd_fu_' + sanitizedLocationName).attr('placeholder');
        }
        return uname;
    };

    var getScore = function(locationName) {
        var sanitizedLocationName = sanitizeString(locationName);
        var score = $('#sd_fs_' + sanitizedLocationName).val();
        if (score === '') {
            score = $('#sd_fs_' + sanitizedLocationName).attr('placeholder');
        }
        return score;
    };

    var doInstructorDashAction = function(action) {
        var user = getUser(action.locationName);
        var pdata = {
            problem_to_reset: action.location,
            unique_student_identifier: user,
            delete_module: action.delete_module,
            only_if_higher: action.only_if_higher,
            score: action.score
        };
        $.ajax({
            type: 'POST',
            url: getURL(action.courseId, action.method),
            data: pdata,
            success: function(data) {
                var text = _.template(action.success_msg, {interpolate: /\{(.+?)\}/g})(
                    {user: user}
                );
                var html = _.template('<p id="idash_msg" class="success">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                    {text: text}
                );
                edx.HtmlUtils.setHtml(
                    $('#result_' + sanitizeString(action.locationName)),
                    edx.HtmlUtils.HTML(html)
                );
            },
            error: function(request, status, error) {
                var responseJSON;
                var errorMsg = _.template(action.error_msg, {interpolate: /\{(.+?)\}/g})(
                    {user: user}
                );
                try {
                    responseJSON = $.parseJSON(request.responseText).error;
                } catch (e) {
                    responseJSON = 'Unknown Error Occurred.';
                }
                var text = _.template('{error_msg} {error}', {interpolate: /\{(.+?)\}/g})(
                    {
                        error_msg: errorMsg,
                        error: gettext(responseJSON)
                    }
                );
                var html = _.template('<p id="idash_msg" class="error">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                    {text: text}
                );
                edx.HtmlUtils.setHtml(
                    $('#result_' + sanitizeString(action.locationName)),
                    edx.HtmlUtils.HTML(html)
                );
            },
            dataType: 'json'
        });
    };

    var reset = function(courseId, locname, location) {
        this.doInstructorDashAction({
            courseId: courseId,
            locationName: locname,
            location: location,
            method: 'reset_student_attempts',
            success_msg: gettext('Successfully reset the attempts for user {user}'),
            error_msg: gettext('Failed to reset attempts for user.'),
            delete_module: false
        });
    };

    var deleteStudentState = function(courseId, locname, location) {
        this.doInstructorDashAction({
            courseId: courseId,
            locationName: locname,
            location: location,
            method: 'reset_student_attempts',
            success_msg: gettext('Successfully deleted student state for user {user}'),
            error_msg: gettext('Failed to delete student state for user.'),
            delete_module: true
        });
    };

    var rescore = function(courseId, locname, location) {
        this.doInstructorDashAction({
            courseId: courseId,
            locationName: locname,
            location: location,
            method: 'rescore_problem',
            success_msg: gettext('Successfully rescored problem for user {user}'),
            error_msg: gettext('Failed to rescore problem for user.'),
            only_if_higher: false
        });
    };

    var rescoreIfHigher = function(courseId, locname, location) {
        this.doInstructorDashAction({
            courseId: courseId,
            locationName: locname,
            location: location,
            method: 'rescore_problem',
            success_msg: gettext('Successfully rescored problem to improve score for user {user}'),
            error_msg: gettext('Failed to rescore problem to improve score for user.'),
            only_if_higher: true
        });
    };

    var overrideScore = function(courseId, locname, location) {
        this.doInstructorDashAction({
            courseId: courseId,
            locationName: locname,
            location: location,
            method: 'override_problem_score',
            success_msg: gettext('Successfully overrode problem score for {user}'),
            error_msg: gettext('Could not override problem score for {user}.'),
            score: getScore(locname)
        });
    };

    return {
        reset: reset,
        deleteStudentState: deleteStudentState,
        rescore: rescore,
        rescoreIfHigher: rescoreIfHigher,
        overrideScore: overrideScore,

        // export for testing
        doInstructorDashAction: doInstructorDashAction,
        getURL: getURL,
        getUser: getUser,
        getScore: getScore,
        sanitizeString: sanitizeString
    };
}());

// Register click handlers
$(document).ready(function() {

    var $mainContainer = $('#main');
    $mainContainer.on('click', '.staff-debug-reset', function() {
        StaffDebug.reset(
            $(this).parent().data('course-id'),
            $(this).parent().data('location-name'),
            $(this).parent().data('location')
        );
        return false;
    });
    $mainContainer.on('click', '.staff-debug-sdelete', function() {
        StaffDebug.deleteStudentState(
            $(this).parent().data('course-id'),
            $(this).parent().data('location-name'),
            $(this).parent().data('location')
        );
        return false;
    });
    $mainContainer.on('click', '.staff-debug-rescore', function() {
        StaffDebug.rescore(
            $(this).parent().data('course-id'),
            $(this).parent().data('location-name'),
            $(this).parent().data('location')
        );
        return false;
    });
    $mainContainer.on('click', '.staff-debug-rescore-if-higher', function() {
        StaffDebug.rescoreIfHigher(
            $(this).parent().data('course-id'),
            $(this).parent().data('location-name'),
            $(this).parent().data('location')
        );
        return false;
    });

    $mainContainer.on('click', '.staff-debug-override-score', function() {
        StaffDebug.overrideScore(
            $(this).parent().data('course-id'),
            $(this).parent().data('location-name'),
            $(this).parent().data('location')
        );
        return false;
    });
});
