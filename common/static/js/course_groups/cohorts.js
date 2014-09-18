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
        var el = $(".cohort_manager");
        // localized jquery
        var $$ = function (selector) {
            return $(selector, el)
        }
        var state_init = "init";
        var state_summary = "summary";
        var state_detail = "detail";
        var state = state_init;
        
        var url = el.data('ajax_url');
        var self = this;

        // Pull out the relevant parts of the html
        // global stuff
        var errors = $$(".errors");

        // cohort summary display
        var summary = $$(".summary");
        var cohorts = $$(".cohorts");
        var show_cohorts_button = $$(".controls .show_cohorts");
        var add_cohort_input = $$(".cohort_name");
        var add_cohort_button = $$(".add_cohort");
        
        // single cohort user display
        var detail = $$(".detail");
        var detail_header = $(".header", detail);
        var detail_users = $$(".users");
        var detail_page_num = $$(".page_num");
        var users_area = $$(".users_area");
        var add_members_button = $$(".add_members");
        var op_results = $$(".op_results");
        var cohort_id = null;
        var cohort_title = null;
        var detail_url = null;
        var page = null;

        // *********** Summary view methods

        function show_cohort(item) {
            // item is a li that has a data-href link to the cohort base url
            var el = $(this);
            cohort_title = el.text();
            detail_url = el.data('href');
            cohort_id = el.data('id');
            state = state_detail;
            render();
            return false;
        }

        function add_to_cohorts_list(item) {
            var li = $('<li><a href="#"></a></li>');
            $("a", li).text(item.name)
                .data('href', url + '/' + item.id)
                .addClass('link')
                .click(show_cohort);
            cohorts.append(li);
        };

        function log_error(msg) {
            errors.empty();
            errors.append($("<li />").text(msg).addClass("error"));
        };
        
        function load_cohorts(response) {
            cohorts.empty();
            if (response && response.success) { 
                response.cohorts.forEach(add_to_cohorts_list);
            } else {
                log_error(response.msg || "There was an error loading cohorts");
            }
            summary.show();
        };


        function added_cohort(response) {
            if (response && response.success) {
                add_to_cohorts_list(response.cohort);
            } else {
                log_error(response.msg || "There was an error adding a cohort");
            }                
        }

        // *********** Detail view methods

        function remove_user_from_cohort(username, cohort_id, row) {
            var delete_url = detail_url + '/delete';
            var data = {'username': username}
            $.post(delete_url, data).done(function() {row.remove()})
                .fail(function(jqXHR, status, error) {
                    log_error('Error removing user ' + username + 
                              ' from cohort. ' + status + ' ' + error);
                });
        }

        function add_to_users_list(item) {
            var tr = $('<tr><td class="name"></td><td class="username"></td>' + 
                       '<td class="email"></td>' + 
                       '<td class="remove"></td></tr>');
            var current_cohort_id = cohort_id;

            $(".name", tr).text(item.name);
            $(".username", tr).text(item.username);
            $(".email", tr).text(item.email);

            $(".remove", tr).html('<a href="#">remove</a>')
                .click(function() { 
                    remove_user_from_cohort(item.username, current_cohort_id, tr);
                    return false;
                });
            
            detail_users.append(tr);
        };

                
        function show_users(response) {
            detail_users.html("<tr><th>Name</th><th>Username</th><th>Email</th></tr>");
            if (response && response.success) { 
                response.users.forEach(add_to_users_list);
                detail_page_num.text("Page " + response.page + " of " + response.num_pages);
            } else {
                log_error(response.msg || 
                          "There was an error loading users for " + cohort.title);
            }
            op_results.empty();
            detail.show();
        }
            

        function added_users(response) {
            op_results.empty();
            if (response && response.success) {
                function add_to_list(text, color) {
                    op_results.append($("<li/>").text(text).css("color", color));
                }
                response.added.forEach(
                    function(item) {
                        add_to_list(
                            "Added: " + item.name + ", " + item.username + ", " + item.email,
                            "green"
                        );
                    }
                );
                response.changed.forEach(
                    function(item) {
                        add_to_list(
                            "Moved from cohort " + item.previous_cohort + ": " + item.name + ", " + item.username + ", " + item.email,
                            "purple"
                        )
                    }
                );
                response.present.forEach(
                    function(item) {
                        add_to_list("Already present: " + item, "black");
                    }
                );
                response.unknown.forEach(
                    function(item) {
                        add_to_list("Unknown user: " + item, "red")
                    }
                );
                users_area.val('')
            } else {
                log_error(response.msg || "There was an error adding users");
            }                
        }

        // ******* Rendering

            
        function render() {
            // Load and render the right thing based on the state
             
            // start with both divs hidden
            summary.hide();
            detail.hide();
            // and clear out the errors
            errors.empty();
            if (state == state_summary) {
                $.ajax(url).done(load_cohorts).fail(function() {
                    log_error("Error trying to load cohorts");
                });
            } else if (state == state_detail) {
                detail_header.text("Members of " + cohort_title);
                $.ajax(detail_url, {data: {page: 1}}).done(show_users).fail(function() {
                    log_error("Error trying to load users in cohort");
                });
            }
        }

        show_cohorts_button.click(function() { 
            state = state_summary;
            render();
            return false;
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
            return false;
        });

        add_members_button.click(function() { 
            var add_url = detail_url + '/add';
            data = {'users': users_area.val()}
            $.post(add_url, data).done(added_users);
            return false;
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

