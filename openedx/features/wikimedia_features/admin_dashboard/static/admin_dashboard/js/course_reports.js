(function() {
    'use strict';
    let getCookie, ReportDownloads, AjaxCall, toggleDisplay;
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
                if (data.downloads.length && $('#report-downloads-table').find('a').length == 0){
                    for (let i = 0; i < data.downloads.length; i++) {
                        $('#report-downloads-table').append(data.downloads[i]['link']);
                        $('#report-downloads-table').append('<br>');
                    }
                }
                else if (data.downloads.length > $('#report-downloads-table').find('a').length){
                    let newReportsFetched = data.downloads.length - $('#report-downloads-table').find('a').length;
                    for (let i = newReportsFetched; i > 0; i--) {
                        $('#report-downloads-table').prepend('<br>');
                        $('#report-downloads-table').prepend(data.downloads[i-1]['link']);
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
                    errorMessage = JSON.parse(error.responseText);
                }
                $('.request-response-error').text(errorMessage);
            },
            success: function(data) {
                $('.request-response').text(data.status);
            }
        });
    };

    setInterval(function() {
        ReportDownloads();
    }, 20000);
    
    toggleDisplay = function(list_of_elements, display_type){
        for (let i = 0; i < list_of_elements.length; i++){
            list_of_elements[i].style.display = display_type;
        }
    }

    $('select').change(function (e) {
        e.preventDefault();
        $('#report-request-response').empty();
        $('#report-request-response-error').empty();
        $('#report-downloads-table').empty();
        let display_type;
        let list_of_elements = $('.single-course-report');
        if ($(this).val())
        {
            if ($(this).val().length> 1) {
                course_name = $(this).val().toString();
                display_type = "none"
                toggleDisplay(list_of_elements, display_type);                
            }
            else {
                course_name = $(this).val()[0];
                display_type = "block";
                toggleDisplay(list_of_elements, display_type);
            }
            endpoint = `/courses/${$(this).val()[0]}/instructor/api/list_report_downloads`;
        }
        else {
            course_name = $('.filter-selectbox').children()[0].value;
            endpoint = `/courses/${course_name}/instructor/api/list_report_downloads`;
        }
    });

    $("input[name='list-profiles-csv']").click(function() {
        let url_for_list_profiles_csv = '/courses/' + course_name + '/instructor/api/get_students_features' + '/csv';
        AjaxCall(url_for_list_profiles_csv);
    });

    $("input[name='calculate-grades-csv']").click(function() {
        let url_for_calculate_grades = '/courses/' + course_name + '/instructor/api/calculate_grades_csv';
        AjaxCall(url_for_calculate_grades);
    });

    $("input[name='list-anon-ids']").click(function() {
        let url_for_list_anon_ids = '/courses/' + course_name + '/instructor/api/get_anon_ids';
        AjaxCall(url_for_list_anon_ids);
    });

    $("input[name='problem-grade-report']").click(function() {
        let url_for_problem_grade_report = '/courses/' + course_name + '/instructor/api/problem_grade_report';
        AjaxCall(url_for_problem_grade_report);
    });

    $("input[name='list-may-enroll-csv']").click(function() {
        let url_for_list_may_enroll = '/courses/' + course_name + '/instructor/api/get_students_who_may_enroll';
        AjaxCall(url_for_list_may_enroll);
    });

    $("input[name='average-calculate-grades-csv']").click(function() {
        let url_for_average_calculate_grades = '/admin_dashboard/average_calculate_grades_csv/' + course_name ;
        AjaxCall(url_for_average_calculate_grades);
    })
}).call(this);
