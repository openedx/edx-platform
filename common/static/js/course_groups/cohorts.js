// structure stolen from http://briancray.com/posts/javascript-module-pattern

var CohortManager = (function ($) {
    // private variables and functions

    // using jQuery
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }  
    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // constructor
    var module = function () {
        var url = $(".cohort_manager").data('ajax_url');
        var self = this;
        var error_list = $(".cohort_errors");
        var cohort_list = $(".cohort_list");
        var cohorts_display = $(".cohorts_display");
        var show_cohorts_button = $(".cohort_controls .show_cohorts");
        var add_cohort_input = $("#cohort-name");
        var add_cohort_button = $(".add_cohort");

        function show_cohort(item) {
            // item is a li that has a data-href link to the cohort base url
            var el = $(this);
            alert("would show you data about " + el.text() + " from " + el.data('href'));
        }

        function add_to_cohorts_list(item) {
            var li = $('<li><a></a></li>');
            $("a", li).text(item.name)
                .data('href', url + '/' + item.id)
                .addClass('link')
                .click(show_cohort);
            cohort_list.append(li);
        };

        function log_error(msg) {
            error_list.empty();
            error_list.append($("<li />").text(msg).addClass("error"));
        };
        
        function load_cohorts(response) {
            cohort_list.empty();
            if (response && response.success) { 
                response.cohorts.forEach(add_to_cohorts_list);
            } else {
                log_error(response.msg || "There was an error loading cohorts");
            }
            cohorts_display.show();
        };

        function added_cohort(response) {
            if (response && response.success) {
                add_to_cohorts_list(response.cohort);
            } else {
                log_error(response.msg || "There was an error adding a cohort");
            }                
        }

        show_cohorts_button.click(function() { 
            $.ajax(url).done(load_cohorts);
        });
        
        add_cohort_input.change(function() {
            if (!$(this).val()) {
                add_cohort_button.removeClass('button').addClass('button-disabled');
            } else {
                add_cohort_button.removeClass('button-disabled').addClass('button');
            }
        });

        add_cohort_button.click(function() { 
            var add_url = url + '/add';
            data = {'name': add_cohort_input.val()}
            $.post(add_url, data).done(added_cohort);
        });

    };

    // prototype
    module.prototype = {
        constructor: module,
    };

    // return module
    return module;
})(jQuery);

$(window).load(function () {
    var my_module = new CohortManager();
})

