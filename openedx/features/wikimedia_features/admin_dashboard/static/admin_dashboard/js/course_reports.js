(function() {
    'use strict';
    let getCookie, ReportDownloads;
    let url = $("input[name='list-profiles-csv']").data('endpoint') + '/csv';
    let endpoint =  $('.report-downloads-table').data('endpoint');

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
                $('#report-downloads-table').empty();
                if (data.downloads.length){
                    for (let i = 0; i < data.downloads.length; i++) {
                        $('#report-downloads-table').append(data.downloads[i]['link']);
                        $('#report-downloads-table').append('<br>');
                    }
                }
            },
            error: function() {
                console.log("There is an error in the list report downloads api")
            }
        });
    };

    $('select').change(function (e) {
        e.preventDefault();
        let course_name = $(this).val();
        url = '/courses/' + course_name + '/instructor/api/get_students_features' + '/csv';
        endpoint = '/courses/' + course_name + '/instructor/api/list_report_downloads';
        $('#report-downloads-table').empty();
    });

    $("input[name='list-profiles-csv']").click(function() {
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
                return $('.request-response-error').css({
                    display: 'block'
                });
            },
            success: function(data) {
                ReportDownloads();
                $('.request-response').text(data.status);
                return $('.msg-confirm').css({
                    display: 'block'
                });
            }
        });
    });

}).call(this);
