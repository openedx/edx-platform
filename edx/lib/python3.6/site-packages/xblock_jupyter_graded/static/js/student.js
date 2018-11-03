function JupyterGradedXBlock(runtime, element, context) {
    var studentUrl = runtime.handlerUrl(element, 'handle_student_nb_upload');
    var id = context.xblock_id;

    var upload_success = function(data, text) {
        var student = $('#student_upload_result_'+id);
        student[0].className = '';
        if (!data.success) {
            student.addClass("my-alert my-alert-danger");
            student.html(data.error);
            $("#student_upload_"+id).prop("disabled", false);
            $("#student_file_"+id).prop("disabled", false);
        } else {
            if (data.autograded_err != null) {
                student.addClass("my-alert my-alert-warning");
				student.html("Notebook Successfully Uploaded and Scored. " +
                    "Please note the following error:<br><br>" + data.autograded_err);
            } else {
				student.addClass("my-alert my-alert-success");
				student.html("Notebook Successfully Uploaded and Scored<br><br>Please see results below");
            }
            $('#student_score_'+id).html(data.score);
            $('#student_attempts_'+id).html(data.attempts);
            $('#submitted_dt_'+id).html(data.submitted_dt);

            if (data.hasOwnProperty('autograded_url')) {
                $("#autograded_wrap_"+id)[0].className = '';
                $("#autograded_nb_url_"+id).attr({
                    "href": data.autograded_url
                });
            }

            if (data.disable_uploads) {
                $("#student_upload_"+id).prop("disabled", true);
                $("#student_file_"+id).prop("disabled", true);
            } else {
                $("#student_upload_"+id).prop("disabled", false);
                $("#student_file_"+id).prop("disabled", false);
            }

            $('#section_scores_'+id).html(data.section_scores);
        }
    }

    var upload_error = function(jqxhr, text) {
        var result = $('#student_upload_result_'+id);
        result[0].className = '';
        result.addClass("my-alert my-alert-danger");
        result.html("An error has occurred while uploading your notebook.<br><br>Please contact your instructor.");
        console.log("Upload Error Occurred: ");
        console.log(jqxhr.responseText);
        $("#student_upload_"+id).prop("disabled", false);
        $("#student_file_"+id).prop("disabled", false);
    }

    var upload_complete = function(data, text) {
        $("#student_loader_"+id).css("animation-play-state", "paused");
        $("#student_loader_"+id).css("visibility", "hidden");
    }

    var student_upload = function() {
        $("#student_loader_"+id).css("animation-play-state", "running");
        $("#student_loader_"+id).css("visibility", "visible");
        $("#student_upload_"+id).prop("disabled", true);
        $("#student_file_"+id).prop("disabled", true);
        var result = $('#student_upload_result_'+id);
        result[0].className = '';
        result.addClass("my-alert my-alert-info");
        result.html("Uploading and evaluating iPython notebook ... Please Wait");

        var f = ($('#student_file_'+id).prop('files')[0]);
        var data = new FormData();
        data.append("file", f)
        $.ajax({
            url: studentUrl,
            type: 'POST',
            data: data, 
            cache: false,
            contentType: false,
            processData: false,
            timeout: 0,
            success: upload_success,
            error: upload_error,
            complete: upload_complete
        });
    };

    $(function ($) {
        $("#student_upload_"+id).click(student_upload);
    });
}
