// Make sure put and post requests are sent with the xsrf cookie
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// Backbone requests
var oldSync = Backbone.sync;
Backbone.sync = function(method, model, options) {
    options.beforeSend = function(xhr) {
        xhr.setRequestHeader('X-CSRFToken', getCookie("_xsrf"));
    };
    return oldSync(method, model, options);
};

$.ajaxPrefilter(function(options, originalOptions, jqXHR){
    if (options['type'].toLowerCase() === "post") {
        jqXHR.setRequestHeader('X-CSRFToken', getCookie("_xsrf"));
    }
});
