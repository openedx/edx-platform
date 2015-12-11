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
