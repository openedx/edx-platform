'use strict';
/**
 * A functional class to encapsulate staff actions within the context of a given course
 * and block.
 *
 * Stateless; please do not add inner variables.
 */
function StaffDebugActions(courseId, locationName, location) {
    var getURL = function(action) {
        return 'courses/' + courseId + '/instructor/api/' + action;
    };

    var sanitizeString = function(string) {
        return string.replace(/[.*+?^:${}()|[\]\\]/g, '\\$&');
    };

    var getUser = function() {
        var sanitizedLocationName = sanitizeString(locationName);
        var uname = $('#sd_fu_' + sanitizedLocationName).val();
        if (uname === '') {
            uname = $('#sd_fu_' + sanitizedLocationName).attr('placeholder');
        }
        return uname;
    };

    var getScore = function() {
        var sanitizedLocationName = sanitizeString(locationName);
        var score = $('#sd_fs_' + sanitizedLocationName).val();
        if (score === '') {
            score = $('#sd_fs_' + sanitizedLocationName).attr('placeholder');
        }
        return score;
    };

    var doInstructorDashAction = function(action) {
        var pdata = {
            problem_to_reset: location,
            unique_student_identifier: getUser(locationName),
            delete_module: action.delete_module,
            only_if_higher: action.only_if_higher,
            score: action.score
        };
        $.ajax({
            type: 'POST',
            url: getURL(action.method),
            data: pdata,
            success: function(data) {
                var text = _.template(action.success_msg, {interpolate: /\{(.+?)\}/g})(
                {user: data.student}
            );
                var html = _.template('<p id="idash_msg" class="success">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                {text: text}
            );
                edx.HtmlUtils.setHtml(
                  $('#result_' + sanitizeString(locationName)),
                  edx.HtmlUtils.HTML(html)
                );
            },
            error: function(request, status, error) {
                var responseJSON;
                try {
                    responseJSON = $.parseJSON(request.responseText);
                } catch (e) {
                    responseJSON = 'Unknown Error Occurred.';
                }
                var text = _.template('{error_msg} {error}', {interpolate: /\{(.+?)\}/g})(
                    {
                        error_msg: action.error_msg,
                        error: gettext(responseJSON)
                    }
            );
                var html = _.template('<p id="idash_msg" class="error">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                {text: text}
            );
                edx.HtmlUtils.setHtml(
                  $('#result_' + sanitizeString(locationName)),
                  edx.HtmlUtils.HTML(html)
                );
            },
            dataType: 'json'
        });
    };

    var reset = function() {
        this.doInstructorDashAction({
            method: 'reset_student_attempts',
            success_msg: gettext('Successfully reset the attempts for user {user}'),
            error_msg: gettext('Failed to reset attempts for user.'),
            delete_module: false
        });
    };

    var deleteStudentState = function() {
        this.doInstructorDashAction({
            method: 'reset_student_attempts',
            success_msg: gettext('Successfully deleted student state for user {user}'),
            error_msg: gettext('Failed to delete student state for user.'),
            delete_module: true
        });
    };

    var rescore = function() {
        this.doInstructorDashAction({
            method: 'rescore_problem',
            success_msg: gettext('Successfully rescored problem for user {user}'),
            error_msg: gettext('Failed to rescore problem for user.'),
            only_if_higher: false
        });
    };

    var rescoreIfHigher = function() {
        this.doInstructorDashAction({
            method: 'rescore_problem',
            success_msg: gettext('Successfully rescored problem to improve score for user {user}'),
            error_msg: gettext('Failed to rescore problem to improve score for user.'),
            only_if_higher: true
        });
    };

    var overrideScore = function() {
        this.doInstructorDashAction({
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
};

// Register click handlers
$(document).ready(function() {
    var $mainContainer = $('#main');

    function staffActionOnClick(elementClass, handlerMethodName) {
        $mainContainer.on('click', elementClass, function() {
            var debugActionsDiv = $(this).parent();
            var staffActions = StaffDebugActions(
                debugActionsDiv.data('course-id'),
                debugActionsDiv.data('location-name'),
                debugActionsDiv.data('location')
            );
            staffActions[handlerMethodName]();
            return false;
        });
    }
    staffActionOnClick(
        '.staff-debug-reset',
        'reset'
    );
    staffActionOnClick(
        '.staff-debug-sdelete',
        'deleteStudentState'
    );
    staffActionOnClick(
        '.staff-debug-rescore',
        'rescore'
    );
    staffActionOnClick(
        '.staff-debug-rescore-if-higher',
        'rescoreIfHigher'
    );
    staffActionOnClick(
        '.staff-debug-override-score',
        'overrideScore'
    );
};
