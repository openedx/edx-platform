(function() {
    'use strict';
    let getCookie, ReportDownloads, AjaxCall;
    let course_name = $('.filter-selectbox').children()[0].value;
    let endpoint =  '/courses/' + course_name + '/instructor/api/list_report_downloads';

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
                }
                if (data.downloads.length && $('#report-downloads-list').find('a').length == 0){
                    for (let i = 0; i < data.downloads.length; i++) {
                        $('#report-downloads-list').append('<li>'+data.downloads[i]['link']+'</li>');
                    }
                }
                else if (data.downloads.length > $('#report-downloads-list').find('a').length){
                    let newReportsFetched = data.downloads.length - $('#report-downloads-list').find('a').length;
                    for (let i = newReportsFetched; i > 0; i--) {
                        $('#report-downloads-list').prepend('<li>'+data.downloads[i-1]['link']+'</li>');
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
                    $('.request-response-error').text(error.responseText);
                }
                $('.request-response-error').text(errorMessage).show();
            },
            success: function(data) {
                $('.request-response').text(data.status).show();
            }
        });
    };

    setInterval(function() {
        ReportDownloads();
    }, 20000);

    $('#select-courses').select2({
        placeholder: "Browse Courses",
    });

    $('select').change(function (e) {
        e.preventDefault();
        $('#report-request-response,#report-request-response-error,#report-downloads-list').empty().hide();
        let display_type;
        let list_of_elements = $('.single-course-report');
        if ($(this).val())
        {
            if ($(this).val().length> 1) {
                course_name = $(this).val().toString();
                list_of_elements.hide();
            }
            else {
                course_name = $(this).val()[0];
                list_of_elements.show();
            }
            endpoint = `/courses/${$(this).val()[0]}/instructor/api/list_report_downloads`;
        }
        else {
            course_name = $('.filter-selectbox').children()[0].value;
            endpoint = `/courses/${course_name}/instructor/api/list_report_downloads`;
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
    })

    $("input[name='progress-report-csv']").click(function() {
        let url_for_average_calculate_grades = '/admin_dashboard/progress_report_csv/' + course_name ;
        AjaxCall(url_for_average_calculate_grades);
    })
}).call(this);
