/*
Cohorts Section
*/
// TODO this file needs to be fully i18n'd
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
        var el = $(".cohort-manager");
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
        var errors = $$(".cohort-errors");

        // cohort summary display
        var summary = $$(".cohort-summary");
        var cohorts = $$(".cohorts");
        var show_cohorts_button = $$(".controls .show-cohorts");
        var add_cohort_input = $$(".cohort-name");
        var add_cohort_button = $$(".add-cohort");
        
        // single cohort user display
        var detail = $$(".cohort-detail");
        var detail_header = $(".cohort-header", detail);
        var detail_users = $$(".cohort-users");
        var detail_page_num = $$(".cohort-page-num");
        var users_area = $$(".cohort-users-area");
        var add_members_button = $$(".add-cohort-members");
        var op_results = $$(".cohort-op-results");
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
            errors.append($("<span />").text(msg).addClass("error"));
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

            $(".remove", tr).html('<a href="#"> <i class="icon-remove-sign"></i> ' + gettext('Remove') + '</a>')
                .click(function() { 
                    remove_user_from_cohort(item.username, current_cohort_id, tr);
                    return false;
                });
            
            detail_users.append(tr);
        };


        function show_users(response) {
            if (response && response.success && response.users.length > 0) { 
		// TODO this should use Slickgrid
		detail_users.html("<tr><th>" + gettext('Name') + "</th><th>" + gettext("Username") + "</th><th>" + gettext("Email") + "</th></tr>");
                response.users.forEach(add_to_users_list);
		p_page_text = gettext("Page <%= cur_page_num %> of <%= total_num_pages %>");
		page_text = _.template(p_page_text, {
		    cur_page_num: response.page,
		    total_num_pages: response.num_pages
		});
                detail_page_num.html("<em>" + page_text + "</em>");
            } else if (response.users.length == 0) {
		// TODO bug: there seems to be a bug where there are no users registered for this cohort,
		// but the users from another cohort display -- along with this message!
		// Further debugging needed.
		p_no_users_text = gettext("There are no users registered for cohort <%= cohort_name %>.");
		no_users_text = _.template(p_no_users_text, {
		    cohort_name: cohort_title
		});
		detail_users.html("<em>" + no_users_text + "</em>");
	    } else {
		p_error_text = gettext("There was an error loading users for cohort <%= cohort_name %>");
		error_text = _.template(p_error_text, {
		    cohort_name: cohort_title
		});
                log_error(response.msg || error_text);
	    }
	    detail.show();
            op_results.empty();
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
		p_header_text = gettext("Members of <%= cohort_name %>");
		header_text = _.template(p_header_text, {
		    cohort_name: cohort_title
		});
                detail_header.text(header_text);
                $.ajax(detail_url).done(show_users).fail(function() {
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
	    // Clear input field
	    add_cohort_input.val('');
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

//$(window).load(function () {
//    var my_module = new CohortManager();
//})

(function() {
  var Cohorts, plantTimeout, std_ajax_err;

  plantTimeout = function() {
    return window.InstructorDashboard.util.plantTimeout.apply(this, arguments);
  };

  std_ajax_err = function() {
    return window.InstructorDashboard.util.std_ajax_err.apply(this, arguments);
  };

  Cohorts = (function() {
    function Cohorts($section) {
      this.$section = $section;
      this.$section.data('wrapper', this);
      this.cohort_manager = new CohortManager();
    }

    Cohorts.prototype.onClickTitle = function() {
	// TODO click the show_cohorts_button here
    };

    return Cohorts;

  })();

  if (typeof _ !== "undefined" && _ !== null) {
    _.defaults(window, {
      InstructorDashboard: {}
    });
    _.defaults(window.InstructorDashboard, {
      sections: {}
    });
    _.defaults(window.InstructorDashboard.sections, {
      Cohorts: Cohorts
    });
  }

}).call(this);
