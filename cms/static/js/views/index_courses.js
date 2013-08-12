function indexCourses(){
    var course = "";
    var url = window.location.host + "/index";
    var courseHashId = $("#index-courses").eq(0).attr("data-hash");
    console.log(url);
    $.ajax({
        type: "POST",
        url: url,
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
