(function($, undefined) {
  var form_ext;
  $.form_ext  = form_ext = {
    ajax: function(options) {
      return $.ajax(options);
    },
    handleRemote: function(element) {
      var method = element.attr('method');
      var url = element.attr('action');
      var data = element.serializeArray();
      var options = {
        type: method || 'GET',
        data: data,
        dataType: 'text json',
        success: function(data, status, xhr) {
          element.trigger("ajax:success", [data, status, xhr]);
        },
        complete: function(xhr, status) {
          element.trigger("ajax:complete", [xhr, status]);
        },
        error: function(xhr, status, error) {
          element.trigger("ajax:error", [xhr, status, error]);
        }
      }
      if(url) { options.url = url; }
      return form_ext.ajax(options)
    },
    CSRFProtection: function(xhr) {
      var token = $.cookie('csrftoken');
      if (token) xhr.setRequestHeader('X-CSRFToken', token);
    }
  }
  $.ajaxPrefilter(function(options, originalOptions, xhr){ if ( !options.crossDomain ) { form_ext.CSRFProtection(xhr); }});
  $(document).delegate('form', 'submit', function(e) {
    var form = $(this),
    remote = form.data("remote") !== undefined;

    if(remote) {
      form_ext.handleRemote(form);
      return false;
    }

  });
})(jQuery);
