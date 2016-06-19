// Build StaffDebug object
var StaffDebug = (function (){

  get_current_url = function() {
    return window.location.pathname;
  };

  get_url = function(action){
    var pathname = this.get_current_url();
    var url = pathname.substr(0,pathname.indexOf('/courseware')) + '/instructor/api/' + action;
    return url;
  };

  sanitized_string = function(string) {
    return string.replace(/[.*+?^:${}()|[\]\\]/g, "\\$&");
  };

  get_user = function(locname){
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
        type: "POST",
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
  };

  sdelete = function(locname, location){
    this.do_idash_action({
        locationName: locname,
        location: location,
        method: 'reset_student_attempts',
        success_msg: gettext('Successfully deleted student state for user {user}'),
        error_msg: gettext('Failed to delete student state.'),
        delete_module: true
    });
  };

  rescore = function(locname, location){
    this.do_idash_action({
        locationName: locname,
        location: location,
        method: 'rescore_problem',
        success_msg: gettext('Successfully rescored problem for user {user}'),
        error_msg: gettext('Failed to rescore problem.'),
        delete_module: false
    });
  };

  return {
      reset: reset,
      sdelete: sdelete,
      rescore: rescore,
      do_idash_action: do_idash_action,
      get_current_url: get_current_url,
      get_url: get_url,
      get_user: get_user,
      sanitized_string:sanitized_string
  }; })();

// Register click handlers
$(document).ready(function() {

    var $courseContent = $('.course-content');
    $courseContent.on("click", '.staff-debug-reset', function() {
        StaffDebug.reset($(this).parent().data('location-name'), $(this).parent().data('location'));
        return false;
    });
    $courseContent.on("click", '.staff-debug-sdelete', function() {
        StaffDebug.sdelete($(this).parent().data('location-name'), $(this).parent().data('location'));
        return false;
    });
    $courseContent.on("click", '.staff-debug-rescore', function() {
        StaffDebug.rescore($(this).parent().data('location-name'), $(this).parent().data('location'));
        return false;
    });
});
