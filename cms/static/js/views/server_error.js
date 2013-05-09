CMS.ServerError = function(model, error) {
    var m = new CMS.Models.SystemFeedback({
        "type": "error",
        "title": "Server Error",
        "message": error.responseText,
        "close": true
    });
    new CMS.Views.Alert({model: m});
    return m;
};
