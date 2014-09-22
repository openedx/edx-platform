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

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type == "PUT") {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$("#email-change-form").submit(function(event) {
    // perform validation?
    $.ajax({
        url: "email_change_request",
        type: "PUT",
        data: {
            new_email: $("#new-email").val(),
            // is this safe?
            password: $("#password").val()
        }
    });
    event.preventDefault();
});
