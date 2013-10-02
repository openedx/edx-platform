function indexCourses(){
    $("#index-courses").attr("disabled", true);
    $("body").css("cursor", "progress");
    var course = "";
    var url = "/index_courseware";
    var courseTitle = $("#index-courses").eq(0).attr("data-course");
    var courseId = $("#course_id").eq(0).attr("value");
    $.ajax({
        type: "POST",
        url: url,
        data: {"course": courseTitle, "course_id": courseId},
        success: success
    });
}

function success(){
    $("body").css("cursor", "auto");
    $("#index-courses").attr("disabled", false);
}

$(document).ready(function() {
    $("#index-courses").eq(0).bind("click", indexCourses);
});
