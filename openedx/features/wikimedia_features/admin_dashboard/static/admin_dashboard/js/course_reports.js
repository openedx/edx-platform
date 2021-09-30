(function() {
    'use strict';
    let getCookie, ReportDownloads, AjaxCall, ReportDownloadsForMultipleCourses;
    let course_name = null;
    let endpoint =  null;
    let report_for_single_courses = null;
    let prev_data_download_len = 0;

    getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    ReportDownloads = function(){
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: endpoint,
            success: function(data) {
                if (data.downloads.length > 0) {
                    $('.download-section, #report-downloads-list').show();
                    if ($('#report-downloads-list').find('a').length == 0){
                        prev_data_download_len = data.downloads.length;
                        for (let i = 0; i < data.downloads.length; i++) {
                            if(data.downloads[i]['name'].split("_")[0] != 'multiple')
                            {
                                $('#report-downloads-list').append('<li>'+data.downloads[i]['link']+'</li>');
                            }
                        }
                    }
                    else if (data.downloads.length > prev_data_download_len){
                        let newReportsFetched = data.downloads.length - prev_data_download_len;
                        prev_data_download_len = data.downloads.length;
                        for (let i = newReportsFetched; i > 0; i--) {
                            if(data.downloads[i-1]['name'].split("_")[0] != 'multiple')
                            {
                                $('#report-downloads-list').prepend('<li>'+data.downloads[i-1]['link']+'</li>');
                            }
                        }
                    }
                }
            },
            error: function() {
                console.log("There is an error in the list report downloads api")
            }
        });
    };

    ReportDownloadsForMultipleCourses = function(){
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: endpoint,
            success: function(data) {
                if (data.downloads.length > 0) {
                    $('.download-section, #report-downloads-list').show();
                    if (report_for_single_courses != false){
                        for (let i = 0; i < data.downloads.length; i++) {
                            if(data.downloads[i]['name'].split("_")[0] == 'multiple')
                            {
                                $('#report-downloads-list').append('<li>'+data.downloads[i]['link']+'</li>');
                            }
                        }
                    }
                    else if (report_for_single_courses == false) {
                        report_for_single_courses = null;
                        if(data.downloads[0]['name'].split("_")[0] == 'multiple')
                        {
                            $('#report-downloads-list').prepend('<li>'+data.downloads[0]['link']+'</li>');
                        }
                    }
                }
            },
            error: function() {
                console.log("There is an error in the list report downloads api")
            }
        });
    };

    AjaxCall = function(url){
        $.ajaxSetup({
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
        });
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: url,
            error: function(error) {
                if (error.responseText) {
                    $('.request-response-error').text(error.responseText).show();
                }
            },
            success: function(data) {
                $('.request-response').text(data.status).show();
            }
        });
    };

    setInterval(function() {
        if(course_name != null)
        {
            if(report_for_single_courses == true)
            {
                ReportDownloads();
            }
            else if(report_for_single_courses == false) {
                ReportDownloadsForMultipleCourses();
            }
        }
    }, 20000);

    $('#select-courses').select2({
        placeholder: "Browse Courses",
    });

    $('select').change(function (e) {
        e.preventDefault();
        let list_of_single_course_elements = $('.single-course-report');
        let list_of_multiple_course_elements = $('.multiple-course-report');
                    prev_data_download_len = 0;
        if ($(this).val())
        {
            $('.btn-primary').attr('disabled', false);
            if ($(this).val().length > 1) {
                course_name = $(this).val().toString();
                list_of_single_course_elements.hide();
                list_of_multiple_course_elements.show();
                if(report_for_single_courses == true)
                {
                    $('#report-request-response,#report-request-response-error,#report-downloads-list').empty().hide();
                    for (let i = 0; i < $("#select-courses")[0].length; i++) {
                        endpoint = `/courses/${$("#select-courses")[0].options[i].value}/instructor/api/list_report_downloads`;
                        ReportDownloadsForMultipleCourses();
                    }
                }
                endpoint = `/courses/${$(this).val()[0]}/instructor/api/list_report_downloads`;
                report_for_single_courses = null;
            }
            else {
                $('#report-request-response,#report-request-response-error,#report-downloads-list').empty().hide();
                course_name = $(this).val()[0];
                report_for_single_courses = true;
                list_of_single_course_elements.show();
                list_of_multiple_course_elements.hide();
                endpoint = `/courses/${$(this).val()[0]}/instructor/api/list_report_downloads`;
                ReportDownloads();
            }
        }
        else {
            list_of_single_course_elements.show();
            list_of_multiple_course_elements.show();
            $('.btn-primary').attr('disabled', true);
            course_name = null;
            endpoint = null;
            report_for_single_courses = null;
            $('#report-request-response,#report-request-response-error,#report-downloads-list').empty().hide();
        }
    });

    $("[name='list-profiles-csv']").click(function() {
        let url_for_list_profiles_csv = '/courses/' + course_name + '/instructor/api/get_students_features' + '/csv';
        AjaxCall(url_for_list_profiles_csv);
    });

    $("[name='calculate-grades-csv']").click(function() {
        let url_for_calculate_grades = '/courses/' + course_name + '/instructor/api/calculate_grades_csv';
        AjaxCall(url_for_calculate_grades);
    });

    $("[name='list-anon-ids']").click(function() {
        let url_for_list_anon_ids = '/courses/' + course_name + '/instructor/api/get_anon_ids';
        AjaxCall(url_for_list_anon_ids);
    });

    $("[name='problem-grade-report']").click(function() {
        let url_for_problem_grade_report = '/courses/' + course_name + '/instructor/api/problem_grade_report';
        AjaxCall(url_for_problem_grade_report);
    });

    $("[name='list-may-enroll-csv']").click(function() {
        let url_for_list_may_enroll = '/courses/' + course_name + '/instructor/api/get_students_who_may_enroll';
        AjaxCall(url_for_list_may_enroll);
    });

    $("[name='average-calculate-grades-csv']").click(function() {
        let url_for_average_calculate_grades = '/admin_dashboard/average_calculate_grades_csv/' + course_name ;
        AjaxCall(url_for_average_calculate_grades);
        report_for_single_courses = false;
    })

    $("[name='progress-report-csv']").click(function() {
        let url_for_average_calculate_grades = '/admin_dashboard/progress_report_csv/' + course_name ;
        AjaxCall(url_for_average_calculate_grades);
    })
}).call(this);
