function indexCourses(){
    var course = "";
    var url = window.location.host + "/index";
    $.ajax({
        type: "POST",
        url: url,
        data: {"course": type_id},
        success: success
    });
}

function success(){
    console.log("Success!");
}

$(document).ready(function() {
    $("#index-courses").unbind();
    $("#index-courses").eq(0).bind("click", indexCourses);
});