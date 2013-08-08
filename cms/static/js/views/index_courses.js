function indexCourses(){
    var course = "";
    var url = window.location.host + "/index";
    var courseHashId = $("#index-courses").attr("data-hash");
    console.log(courseHashId)
    $.ajax({
        type: "POST",
        url: "http://localhost:8000/index",
        data: {"course": courseHashId},
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
