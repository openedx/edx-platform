// Build StaffDebug object
var StaffDebug = (function (){
    "use strict";

  var get_current_url = function() {
    return window.location.pathname;
  };

  var sanitized_string = function(string) {
    return string.replace(/[.*+?^:${}()|[\]\\]/g, "\\$&");
  };

  var get_user = function(locname){
    locname = sanitized_string(locname);
    var uname = $('#sd_fu_' + locname).val();
    if (uname===""){
        uname =  $('#sd_fu_' + locname).attr('placeholder');
    }
    return uname;
  };

  do_idash_action = function(action){
    var pdata = {
        'problem_to_reset': action.location,
        'unique_student_identifier': get_user(action.locationName),
        'delete_module': action.delete_module
    };
    $.ajax({
        type: "GET",
        url: get_url(action.method),
        data: pdata,
        success: function(data){
            var text = _.template(action.success_msg, {interpolate: /\{(.+?)\}/g})(
                {user: data.student}
            );
            var html = _.template('<p id="idash_msg" class="success">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                {text: text}
            );
            $("#result_"+sanitized_string(action.locationName)).html(html);
        },
        error: function(request, status, error) {
            var response_json;
            try {
                response_json = $.parseJSON(request.responseText);
            } catch(e) {
                response_json = { error: gettext('Unknown Error Occurred.') };
            }
            var text = _.template('{error_msg} {error}', {interpolate: /\{(.+?)\}/g})(
                {
                    error_msg: action.error_msg,
                    error: response_json.error
                }
            );
            var html = _.template('<p id="idash_msg" class="error">{text}</p>', {interpolate: /\{(.+?)\}/g})(
                {text: text}
            );
            $("#result_"+sanitized_string(action.locationName)).html(html);

        },
        dataType: 'json'
    });
  };

  reset = function(locname, location){
    this.do_idash_action({
        locationName: locname,
        location: location,
        method: 'reset_student_attempts',
        success_msg: gettext('Successfully reset the attempts for user {user}'),
        error_msg: gettext('Failed to reset attempts.'),
        delete_module: false
    });

  var get_url = function(action){
    var problem_to_reset = encodeURIComponent(action.location);
    var unique_student_identifier = get_user(action.locationName);
    var pathname = get_current_url();
    var url = pathname.substr(0,pathname.indexOf('/courseware')) +
        '/instructor'+ '?unique_student_identifier=' + unique_student_identifier +
        '&problem_to_reset=' + problem_to_reset;
    return url;
  };

  var goto_student_admin = function(location) {
    window.location = location;
  };

  var student_grade_adjustemnts = function(locname, location){
    var action = {locationName: locname, location: location};
    var instructor_tab_url = get_url(action);
    this.goto_student_admin(instructor_tab_url + '#view-student_admin');
  };

  return {
      student_grade_adjustemnts: student_grade_adjustemnts,
      goto_student_admin: goto_student_admin,
      get_current_url: get_current_url,
      get_url: get_url,
      get_user: get_user,
      sanitized_string: sanitized_string
  }; })();

// Register click handlers
$(document).ready(function() {
    "use strict";

    var $courseContent = $('.course-content');
    $courseContent.on("click", '.staff-debug-grade-adjustments', function() {
        StaffDebug.student_grade_adjustemnts($(this).parent().data('location-name'), $(this).parent().data('location'));
        return false;
    });
});
