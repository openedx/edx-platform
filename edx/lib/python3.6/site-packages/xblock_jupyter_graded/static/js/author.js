function JupyterGradedXBlock(runtime, element, context) {
    var instructorUrl = runtime.handlerUrl(element, 'handle_instructor_nb_upload');
    var requirementsUrl = runtime.handlerUrl(element, 'handle_requirements_upload');
    instructorUrl = instructorUrl.replace("/preview", "");
    var id = context.xblock_id;

    var inst_upload_success = function(data, text) {
        var inst = $('#inst_upload_result_'+id);
        inst[0].className = '';
        if (!data.success) {
            $('#instructor_upload_'+id).prop("disabled", false);
            $('#instructor_file_'+id).prop("disabled", false);
            inst.addClass("my-alert my-alert-danger");
            inst.html(data.error);

        } else {
            inst.addClass("my-alert my-alert-success");
            inst.html("Notebook Successfully Uploaded");
            $('#nb_name_'+id).html(data.nb_name);
            $('#nb_upload_date_'+id).html(data.nb_upload_date);
            $('#max_nb_score_'+id).html(data.max_score);
            $('#instructor_nb_url_'+id).attr({
                "href": data.instructor_download_url
            });
            $('#instructor_nb_url_'+id).html("Download");
            $('#student_nb_url_'+id).attr({
                "href": data.student_download_url
            });
            $('#student_nb_url_'+id).html("Download Student Notebook");
            $('#instructor_upload_'+id).prop("disabled", true);
            $('#instructor_file_'+id).prop("disabled", true);
        }
    }

    var req_upload_success = function(data, text) {
        console.log("Requirements successfully uploaded");
        var req = $('#req_upload_result_'+id);
        $('#requirements_upload_'+id).prop("disabled", true);
        $('#requirements_file_'+id).prop("disabled", true);
        req[0].className = '';
        if (!data.success) {
            req.addClass("my-alert my-alert-danger");
            req.html(data.error);
        } else {
            req.className = '';
            req.addClass("my-alert my-alert-success");
            req.html("Requirements Successfully Uploaded");
            $('#requirements_'+id).html(data.requirements);
        }
    }

    var inst_upload_error = function(jqxhr, text) {
        $('#instructor_upload_'+id).prop("disabled", false);
        $('#instructor_file_'+id).prop("disabled", false);
        console.log("Error occurred while uploading instructor notebook");
        console.log("Status: " + jqxhr.status);
        console.log(jqxhr.responseText);
        var result = $('#inst_upload_result_'+id);
        result[0].className = '';
        result.addClass("my-alert my-alert-danger");
        result.html("An error occurred while uploading.<br><br>Please see the javascript console and/or EdX CMS Logs for more information.");
    }

    var req_upload_error = function(jqxhr, text) {
        var result = $('#req_upload_result_'+id);
        console.log("Error occurred while uploading requirements.txt");
        console.log("Status: " + jqxhr.status);
        console.log(jqxhr.responseText);
        result[0].className = '';
        result.addClass("my-alert my-alert-danger");
        result.html("An error occurred while uploading.<br><br>Please see the javascript console and/or EdX CMS Logs for more information.");
    }

    var inst_upload_complete = function(data, text) {
        $("#inst_loader_"+id).css("animation-play-state", "paused");
        $("#inst_loader_"+id).css("visibility", "hidden");
    }

    var req_upload_complete = function(data, text) {
        $("#req_loader_"+id).css("animation-play-state", "paused");
        $("#req_loader_"+id).css("visibility", "hidden");
        $('#requirements_upload_'+id).prop("disabled", false);
        $('#requirements_file_'+id).prop("disabled", false);
    }

    var instructor_upload = function() {
        $('#instructor_upload_'+id).prop("disabled", true);
        $('#instructor_file_'+id).prop("disabled", true);
        $("#inst_loader_"+id).css("animation-play-state", "running");
        $("#inst_loader_"+id).css("visibility", "visible");
        var result = $('#inst_upload_result_'+id);
        result[0].className = '';
        result.addClass("my-alert my-alert-info");
        result.html("Uploading and evaluating iPython Notebook ... Please Wait");

        var f = ($('#instructor_file_'+id).prop('files')[0]);
        var data = new FormData();
        data.append("file", f)
        $.ajax({
            url: instructorUrl,
            type: 'POST',
            data: data, 
            cache: false,
            contentType: false,
            processData: false,
            timeout: 0,
            success: inst_upload_success,
            error: inst_upload_error,
            complete: inst_upload_complete
        });
    };

    var requirements_upload = function() {
        $("#req_loader_"+id).css("animation-play-state", "running");
        $("#req_loader_"+id).css("visibility", "visible");
        $('#requirements_upload_'+id).prop("disabled", true);
        $('#requirements_file_'+id).prop("disabled", true);
        var result = $('#req_upload_result_'+id);
        result[0].className = '';
        result.addClass("my-alert my-alert-info");
        result.html("Uploading Requirements and building environment ... Please Wait");

        var f = ($('#requirements_file_'+id).prop('files')[0]);
        var data = new FormData();
        data.append("file", f)
        $.ajax({
            url: requirementsUrl,
            type: 'POST',
            data: data, 
            cache: false,
            contentType: false,
            processData: false,
            success: req_upload_success,
            error: req_upload_error,
            complete: req_upload_complete
        });
    };

    $(function ($) {
        $("#instructor_upload_"+id).click(instructor_upload);
        $("#requirements_upload_"+id).click(requirements_upload);
    });
}
