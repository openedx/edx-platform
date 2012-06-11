$(function() {
  //This is used to scroll error divs to the user's attention. It can be removed when we switch to the branch with jQuery.ScrollTo
  jQuery.fn.scrollMinimal = function(smooth) {
    var cTop = this.offset().top;
    var cHeight = this.outerHeight(true);
    var windowTop = $(window).scrollTop();
    var visibleHeight = $(window).height();

    if (cTop < windowTop) {
      $('body').animate({
        'scrollTop': cTop
      }, 'slow', 'swing');
    } else if (cTop + cHeight > windowTop + visibleHeight) {
      $('body').animate({
        'scrollTop': cTop - visibleHeight + cHeight
      }, 'slow', 'swing');
    }
  };

  var get_survey_data = function() {
      var values = {};

      //First we set the value of every input to null. This assures that even
      //if a checkbox isn't checked or a question isn't answered, its name is
      //still in the dictionary so we know the question was on the form.
      var inputs = $("#survey_fieldset :input");
      inputs.each(function(index, element) {
        values[element.getAttribute("name")] = null;
      });

      //Grab the values from the survey_fieldset
      var serializedArray = inputs.serializeArray();
      for (var i = 0; i < serializedArray.length; i++) {
        var key = serializedArray[i]['name'];
        var value = serializedArray[i]['value'];
        if (key in values && values[key] != null) {
          values[key].push(value);
        } else {
          values[key] = [value];
        }
      }

      return JSON.stringify(values);
  };

  $("#cert_request_form").submit(function() {
    var values = {
      'cert_request_honor_code_verify': $("#cert_request_honor_code_verify").is(':checked'),
      'cert_request_name_verify': $("#cert_request_name_verify").is(':checked'),
      'cert_request_id_verify': $("#cert_request_id_verify").is(':checked'),
      //Notice that if the survey is present, it's data is in here! That is important
      'survey_results': get_survey_data(),
    };

    postJSON('/certificate_request', values, function(data) {
      if (data.success) {
        $("#cert_request").html("<h1>Certificate Request Received</h1><p>Thank you! We will let you know when the certificate is ready to download from the <a href='/profile'>Profile page</a>.</p>");
      } else {
        $("#cert_request_error").html(data.error).scrollMinimal();
      }
    });
    log_event("certificate_request", values);
    return false;
  });

  $("#survey_form").submit(function() {
    var values = { 'survey_results': get_survey_data() };

    postJSON('/exit_survey', values, function(data) {
      if (data.success) {
        $("#survey").html("<h1>Survey Response Recorded</h1><p>Thank you for filling out the survey! You can now return to the <a href='/profile'>Profile page</a>.</p>");
      } else {
        $("#survey_error").html(data.error).scrollMinimal();
      }
    });
    log_event("exit_survey_submission", values);
    return false;
  });
});
